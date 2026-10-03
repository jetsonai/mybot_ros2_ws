"""Gazebo Classic .world -> Gazebo Sim(Fortress) .sdf 변환기

교재 8.3 처럼 Gazebo Classic 의 Building Editor 로 만든 월드를
새 Gazebo(mybot_gz_ws)에서 쓸 수 있게 바꿉니다.

사용법:
  ros2 run mybot_gazebo_ros2 convert_world ~/myworld.world \
      ~/mybot_gz_ws/src/mybot_gazebo_ros2/worlds/myworld.sdf
  (출력 경로를 생략하면 입력 파일 옆에 같은 이름의 .sdf 로 저장)

하는 일:
  - 물체 위치는 파일 끝 <state>(Gazebo 에서 실제로 옮겨 놓은 위치)를 사용
  - box / cylinder / sphere 형상만 변환 (mesh 등은 건너뛰고 경고 출력)
  - 모든 물체는 고정(static) 장애물로 변환
  - Gazebo/Bricks 같은 Classic 머티리얼 스크립트는 비슷한 단색으로 대체
  - LiDAR/IMU/물리에 필요한 시스템 플러그인 추가
"""
import math
import os
import sys
import xml.etree.ElementTree as ET

COLORS = {
    'Gazebo/Bricks': '0.62 0.32 0.22 1',
    'Gazebo/Grey': '0.6 0.6 0.6 1',
    'Gazebo/DarkGrey': '0.35 0.35 0.35 1',
    'Gazebo/White': '0.95 0.95 0.95 1',
    'Gazebo/Black': '0.1 0.1 0.1 1',
    'Gazebo/Wood': '0.55 0.38 0.2 1',
    'Gazebo/WoodFloor': '0.55 0.38 0.2 1',
    'Gazebo/Red': '0.8 0.1 0.1 1',
    'Gazebo/Green': '0.1 0.7 0.1 1',
    'Gazebo/Blue': '0.1 0.2 0.8 1',
    'Gazebo/Yellow': '0.9 0.85 0.1 1',
    'Gazebo/Orange': '1.0 0.45 0.05 1',
}
DEFAULT_COLOR = '0.6 0.6 0.6 1'

TEMPLATE = '''<?xml version="1.0" ?>
<!-- {src} 에서 convert_world 로 변환한 Gazebo Sim(Fortress) 월드 -->
<sdf version="1.7">
  <world name="default">

    <plugin filename="ignition-gazebo-physics-system"
            name="ignition::gazebo::systems::Physics"/>
    <plugin filename="ignition-gazebo-user-commands-system"
            name="ignition::gazebo::systems::UserCommands"/>
    <plugin filename="ignition-gazebo-scene-broadcaster-system"
            name="ignition::gazebo::systems::SceneBroadcaster"/>
    <!-- gpu_lidar 용. WSL2 에서는 ogre2 가 죽는 경우가 많아 ogre 사용 -->
    <plugin filename="ignition-gazebo-sensors-system"
            name="ignition::gazebo::systems::Sensors">
      <render_engine>ogre</render_engine>
    </plugin>
    <plugin filename="ignition-gazebo-imu-system"
            name="ignition::gazebo::systems::Imu"/>

    <physics name="1ms" type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <scene>
      <ambient>0.4 0.4 0.4 1</ambient>
      <background>0.7 0.7 0.7 1</background>
      <shadows>false</shadows>
    </scene>

    <light name="sun" type="directional">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.5 0.1 -0.9</direction>
    </light>

    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><plane><normal>0 0 1</normal><size>100 100</size></plane></geometry>
          <surface><friction><ode><mu>100</mu><mu2>50</mu2></ode></friction></surface>
        </collision>
        <visual name="visual">
          <geometry><plane><normal>0 0 1</normal><size>100 100</size></plane></geometry>
          <material><ambient>0.8 0.8 0.8 1</ambient><diffuse>0.8 0.8 0.8 1</diffuse></material>
        </visual>
      </link>
    </model>

{models}
  </world>
</sdf>
'''


# ---------- pose helpers (x y z roll pitch yaw) ----------
def _parse_pose(el):
    if el is None or not (el.text or '').strip():
        return [0.0] * 6
    v = [float(x) for x in el.text.split()]
    return (v + [0.0] * 6)[:6]


def _rot(r, p, y):
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return [[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
            [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
            [-sp, cp * sr, cp * cr]]


def _compose(a, b):
    """world pose of b, where b is expressed in frame a"""
    ra, rb = _rot(*a[3:]), _rot(*b[3:])
    t = [a[i] + sum(ra[i][k] * b[k] for k in range(3)) for i in range(3)]
    m = [[sum(ra[i][k] * rb[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    pitch = math.asin(max(-1.0, min(1.0, -m[2][0])))
    roll = math.atan2(m[2][1], m[2][2])
    yaw = math.atan2(m[1][0], m[0][0])
    return t + [roll, pitch, yaw]


def _fmt(v):
    return ' '.join(f'{x:.6g}' for x in v)


# ---------- geometry / material ----------
def _geometry(g):
    if g is None:
        return None
    if g.find('box') is not None:
        return f'<box><size>{g.find("box/size").text.strip()}</size></box>'
    if g.find('cylinder') is not None:
        c = g.find('cylinder')
        return (f'<cylinder><radius>{c.find("radius").text.strip()}</radius>'
                f'<length>{c.find("length").text.strip()}</length></cylinder>')
    if g.find('sphere') is not None:
        return f'<sphere><radius>{g.find("sphere/radius").text.strip()}</radius></sphere>'
    return None


def _color(visual):
    mat = visual.find('material')
    if mat is None:
        return DEFAULT_COLOR
    name = mat.find('script/name')
    if name is not None and name.text:
        return COLORS.get(name.text.strip(), DEFAULT_COLOR)
    for tag in ('diffuse', 'ambient'):
        el = mat.find(tag)
        if el is not None and el.text:
            return el.text.strip()
    return DEFAULT_COLOR


def convert(src, dst):
    world = ET.parse(src).getroot().find('world')
    if world is None:
        raise SystemExit(f'<world> 태그가 없습니다: {src}')

    state_model, state_link = {}, {}
    state = world.find('state')
    if state is not None:
        for m in state.findall('model'):
            state_model[m.get('name')] = _parse_pose(m.find('pose'))
            for l in m.findall('link'):
                state_link[(m.get('name'), l.get('name'))] = _parse_pose(l.find('pose'))

    out_models, warnings, n_shapes = [], [], 0
    for m in world.findall('model'):
        mname = m.get('name')
        if mname == 'ground_plane':
            continue
        mpose = state_model.get(mname, _parse_pose(m.find('pose')))
        links = []
        for l in m.findall('link'):
            lname = l.get('name')
            lpose = state_link.get((mname, lname)) or _compose(mpose, _parse_pose(l.find('pose')))
            parts = []
            for kind in ('collision', 'visual'):
                for i, el in enumerate(l.findall(kind)):
                    geo = _geometry(el.find('geometry'))
                    if geo is None:
                        warnings.append(f'{mname}/{lname}/{el.get("name")}: 지원하지 않는 형상이라 건너뜀')
                        continue
                    pose = _fmt(_parse_pose(el.find('pose')))
                    if kind == 'visual':
                        c = _color(el)
                        parts.append(f'        <visual name="visual_{i}"><pose>{pose}</pose>'
                                     f'<geometry>{geo}</geometry>'
                                     f'<material><ambient>{c}</ambient><diffuse>{c}</diffuse></material></visual>')
                    else:
                        n_shapes += 1
                        parts.append(f'        <collision name="collision_{i}"><pose>{pose}</pose>'
                                     f'<geometry>{geo}</geometry></collision>')
            if parts:
                links.append(f'      <link name="{lname}">\n        <pose>{_fmt(lpose)}</pose>\n'
                             + '\n'.join(parts) + '\n      </link>')
        if links:
            out_models.append(f'    <model name="{mname}">\n      <static>true</static>\n'
                              + '\n'.join(links) + '\n    </model>')

    if not out_models:
        raise SystemExit('변환할 물체가 없습니다 (box/cylinder/sphere 형상만 지원).')

    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    with open(dst, 'w') as f:
        f.write(TEMPLATE.format(src=os.path.basename(src), models='\n'.join(out_models)))
    for w in warnings:
        print('[경고]', w)
    print(f'변환 완료: {dst}  (물체 {len(out_models)}개, 충돌 형상 {n_shapes}개)')


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return
    src = os.path.expanduser(argv[0])
    dst = os.path.expanduser(argv[1]) if len(argv) > 1 else os.path.splitext(src)[0] + '.sdf'
    convert(src, dst)


if __name__ == '__main__':
    main()
