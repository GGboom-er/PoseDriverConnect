#!/usr/bin/env python
# _*_ coding:utf8 _*_
"""
Scripts :    maya_utils
Author  :    zhoujunjie(Jesse Chou)
Date    :    2025/8/27 
QQ      :    375714316
E-Mail  :    JesseChou0612@gmail.com or 375714316@qq.com
"""
from maya import cmds
import maya.api.OpenMaya as om


def get_offset_matrix(base_obj, target_obj):
    """
    获取子骨骼相对于父骨骼的偏移矩阵
    :param base_obj: 需要求偏移向量的基础物体，基于此物体，求目标物体的偏移向量
    :param target_obj: 目标物体
    :return: MMatrix 偏移矩阵
    """
    # 获取矩阵
    parent_m = om.MMatrix(cmds.xform(base_obj, q=True, ws=True, m=True))
    child_m = om.MMatrix(cmds.xform(target_obj, q=True, ws=True, m=True))
    # 偏移矩阵 = 父的逆矩阵 * 子矩阵
    offset_m = parent_m.inverse() * child_m
    return offset_m


class SolverSwitchOld(object):
    @property
    def sides(self):
        return ['_L', '_R']

    @property
    def parts(self):
        base_parts = ['Ankle', 'Elbow', 'Hip', 'Knee', 'Scapula', 'Shoulder', 'Wrist']
        finger_parts = [f'{x}Finger{y}' for x in ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky'] for y in range(1, 4)]
        return base_parts + finger_parts

    def check_solver_node(self, side, part):
        solver_node = ''
        if side in self.sides and part in self.parts:
            solver_node = f"{part}{side}_UERBFSolver"
            # 验证解算器节点
            if not cmds.objExists(solver_node) or cmds.nodeType(solver_node) != "UERBFSolverNode":
                print(f"× 节点 {solver_node} 不存在或类型不匹配")
                return ''
        return solver_node

    def switch_to_matrix(self, side, part):
        solver_node = self.check_solver_node(side, part)
        if solver_node:
            fk_node = f"FK{part}{side}"
            if not cmds.objExists(fk_node) or cmds.nodeType(fk_node) != "transform":
                print(f"× 默认模式：FK节点 {fk_node} 不存在或类型错误")
                return

                # 验证当前FK连接
            current_conn = cmds.listConnections(
                f"{solver_node}.inputs[0]",
                source=True,
                destination=False
            )
            if not current_conn or current_conn[0] != fk_node:
                print(f"× 默认模式：{solver_node}.inputs[0] 未连接 {fk_node}")
                return

                # 查找Matrix源节点
            matrix_source = None
            priority_nodes = [
                f"{part}QRotateMMTwist{side}",
                f"{part}{side}DMMMrotateZ"
            ]

            for node in priority_nodes:
                if cmds.objExists(node):
                    matrix_source = node
                    break

            if not matrix_source:
                print(f"× 默认模式：{part}{side} 未找到Matrix源节点")
                return

                # 执行Matrix连接
            try:
                cmds.connectAttr(
                    f"{matrix_source}.matrixSum",
                    f"{solver_node}.inputs[0]",
                    force=True  # 强制断开原有连接
                )
                print(f"√ Matrix连接：{matrix_source}.matrixSum -> {solver_node}.inputs[0]")
            except Exception as e:
                print(f"× Matrix连接失败: {str(e)}")

    def switch_to_fk(self, side, part):
        solver_node = self.check_solver_node(side, part)
        if solver_node:
            # 查找可能的Matrix源节点
            matrix_source = None
            priority_nodes = [
                f"{part}QRotateMMTwist{side}",
                f"{part}{side}DMMMrotateZ"
            ]
            # 检查存在的Matrix源节点
            for node in priority_nodes:
                if cmds.objExists(node):
                    matrix_source = node
                    break

            if not matrix_source:
                print(f"× 反向模式：{part}{side} 未找到Matrix源节点")
                return

                # 获取当前连接信息
            current_conn = cmds.listConnections(
                f"{solver_node}.inputs[0]",
                source=True,
                destination=False,
                plugs=True
            )

            # 验证当前Matrix连接
            if not current_conn or not current_conn[0].startswith(f"{matrix_source}.matrixSum"):
                print(f"× 反向模式：{solver_node}.inputs[0] 未连接到 {matrix_source}.matrixSum")
                return

                # 准备FK节点
            fk_node = f"FK{part}{side}"
            if not cmds.objExists(fk_node) or cmds.nodeType(fk_node) != "transform":
                print(f"× 反向模式：FK节点 {fk_node} 不存在或类型错误")
                return

                # 执行反向连接操作
            try:
                # 断开Matrix连接
                cmds.disconnectAttr(current_conn[0], f"{solver_node}.inputs[0]")
                # 连接FK的世界矩阵
                cmds.connectAttr(
                    f"{fk_node}.matrix",
                    f"{solver_node}.inputs[0]",
                    force=True
                )
                print(f"√ 反向连接：{fk_node}.matrix -> {solver_node}.inputs[0]")
            except Exception as e:
                print(f"× 反向连接失败: {str(e)}")

    def switch_all_to_matrix(self):
        for side in self.sides:
            for part in self.parts:
                self.switch_to_matrix(side, part)

    def switch_all_to_fk(self):
        for side in self.sides:
            for part in self.parts:
                self.switch_to_fk(side, part)


class ControlSwitch(object):
    def __init__(self):
        self.sides = ["L", "R"]
        self.parts = ["Arm", "Leg"]
        self.__rbf_nodes = []

    @property
    def rbf_nodes(self):
        if not self.__rbf_nodes:
            self.__rbf_nodes = cmds.ls(type="UERBFSolverNode")
        return self.__rbf_nodes

    def get_rbf_control_info(self, rbf_node):
        info = []
        if rbf_node in self.rbf_nodes:
            con_list = cmds.listConnections(f'{rbf_node}.outputs[0]', s=False, d=True, p=False)
            con_list.sort()
            blend_nodes = list(set(con_list))
            for blend_node in blend_nodes:
                dmt_node = cmds.listConnections(f'{blend_node}.outMatrix', s=False, d=True, p=False)
                trans = cmds.listConnections(f'{blend_node}.drivenTransform', s=False, d=True, p=False)
                if dmt_node and trans:
                    info.append(
                        {'blend_node': blend_node, 'dmt_node': dmt_node[0], 'trans': trans[0]}
                    )
        return info

    def get_control(self, name):
        sdk_node = ''
        if name.startswith('SDKFK'):
            new_node = name.replace('SDKFK', 'FK')
            if cmds.objExists(new_node):
                sdk_node = new_node
        return sdk_node

    def get_sdk_node(self, name):
        sdk_node = ''
        if name.startswith('FK'):
            new_node = name.replace('FK', 'SDKFK')
            if cmds.objExists(new_node):
                sdk_node = new_node
        return sdk_node

    def switch_control_mode(self, rbf_node, mode=0):
        """
        # 切换控制模式
        :param rbf_node: RBF节点
        :param mode: 控制模式 0:sdk控制模式
                            1:fk控制模式
        """
        if rbf_node in self.rbf_nodes:
            rbf_info = self.get_rbf_control_info(rbf_node)
            for info in rbf_info:
                trans_node = info.get('trans')
                if mode == 0:
                    new_trans = self.get_sdk_node(trans_node)
                elif mode == 1:
                    new_trans = self.get_control(trans_node)
                else:
                    new_trans = ''
                if new_trans:
                    pose_attr = f'{new_trans}.poseBlender'
                    if not cmds.objExists(pose_attr):
                        cmds.addAttr(new_trans, ln='poseBlender', at='message')
                    blend_node = info.get('blend_node')
                    dmt_node = info.get('dmt_node')
                    if blend_node and dmt_node:
                        cmds.connectAttr(f'{blend_node}.drivenTransform', pose_attr, f=True)
                        cmds.connectAttr(f'{dmt_node}.outputTranslate', f'{new_trans}.translate', f=True)
                        cmds.connectAttr(f'{dmt_node}.outputRotate', f'{new_trans}.rotate', f=True)
                        cmds.connectAttr(f'{dmt_node}.outputScale', f'{new_trans}.scale', f=True)
                    # 断掉原始transform连接
                    try:
                        cmds.disconnectAttr(f'{blend_node}.drivenTransform', f'{trans_node}.poseBlender')
                        cmds.disconnectAttr(f'{dmt_node}.outputTranslate', f'{trans_node}.translate')
                        cmds.disconnectAttr(f'{dmt_node}.outputRotate', f'{trans_node}.rotate')
                        cmds.disconnectAttr(f'{dmt_node}.outputScale', f'{trans_node}.scale')
                        cmds.setAttr(f'{trans_node}.t', 0, 0, 0, type='double3')
                        cmds.setAttr(f'{trans_node}.r', 0, 0, 0, type='double3')
                        cmds.setAttr(f'{trans_node}.s', 1, 1, 1, type='double3')
                    except Exception as e:
                        print(e)

    def switch_to_sdk(self, rbf_node):
        self.switch_control_mode(rbf_node, mode=0)

    def switch_to_fk(self, rbf_node):
        self.switch_control_mode(rbf_node, mode=1)

    def switch_all_to_sdk(self):
        for rbf_node in self.rbf_nodes:
            self.switch_to_sdk(rbf_node)

    def switch_all_to_fk(self):
        for rbf_node in self.rbf_nodes:
            self.switch_to_fk(rbf_node)


class RigSystem(object):
    def __init__(self, name=None):
        self.__name = name or ''
        self.__side = ''
        self.__part = ''
        self.__joint = ''
        self.__parent_joint = ''
        self.__fk = ''
        self.__sdk = ''
        self.analyse()

    @property
    def name(self):
        # 部位名称
        return self.__name

    @property
    def side(self):
        if self.name:
            if self.name.endswith('_L'):
                self.__side = '_L'
            elif self.name.endswith('_R'):
                self.__side = '_R'
            elif self.name.endswith('_M'):
                self.__side = '_M'
            else:
                self.__side = ''
        else:
            self.__side = ''
        return self.__side

    @property
    def joint(self):
        # 骨骼名称
        if self.name:
            if not self.__joint:
                temps = self.name.split('FK')
                temp = temps[-1]
                if cmds.objExists(temp):
                    if cmds.nodeType(temp) == 'joint':
                        self.__joint = temp
        else:
            self.__joint = ''
        return self.__joint

    @property
    def parent_joint(self):
        if self.joint:
            if not self.__parent_joint:
                parents = cmds.listRelatives(self.joint, p=True)
                if parents:
                    self.__parent_joint = parents[0]
        else:
            self.__parent_joint = ''
        return self.__parent_joint

    @property
    def part(self):
        if self.joint:
            if self.side:
                self.__part = self.joint.replace(self.side, '')
            else:
                self.__part = self.joint
        else:
            self.__part = ''
        return self.__part

    @property
    def fk(self):
        # fk控制器名称
        if self.joint:
            if not self.__fk:
                fk_name = f'FK{self.joint}'
                if cmds.objExists(fk_name):
                    self.__fk = fk_name
        else:
            self.__fk = ''
        return self.__fk

    @property
    def sdk(self):
        # sdk控制器组名称
        if self.joint:
            if not self.__sdk:
                sdk_name = f'SDKFK{self.joint}'
                if cmds.objExists(sdk_name):
                    self.__sdk = sdk_name
        else:
            self.__sdk = ''
        return self.__sdk

    @property
    def mult_matrix(self):
        node = f'{self.part}MM{self.side}'
        if not cmds.objExists(node):
            cmds.createNode('multMatrix', n=node)
            cons = cmds.listConnections(node, s=True, d=False)
            if not cons:
                cmds.connectAttr(f'{self.fk}.worldMatrix[0]', f'{node}.matrixIn[0]', f=True)
            if self.parent_joint:
                cmds.connectAttr(f'{self.parent_joint}.worldInverseMatrix[0]', f'{node}.matrixIn[1]', f=True)
        return node

    @property
    def twist_matrix(self):
        node = f'{self.part}QRotateMMTwist{self.side}'
        if not cmds.objExists(node):
            cmds.createNode('multMatrix', n=node)
            if self.parent_joint:
                offset_matrix = get_offset_matrix(self.parent_joint, self.joint)
                cmds.setAttr(f'{node}.matrixIn[1]', list(offset_matrix), type='matrix')
        return node

    def change_name(self, new_name):
        """
        修改部位名称
        :param new_name: 新部位名称
        :return:
        """
        if new_name and new_name != self.name:
            self.__name = new_name
            self.__side = ''
            self.__part = ''
            self.__joint = ''
            self.__parent_joint = ''
            self.__fk = ''
            self.__sdk = ''
            self.analyse()

    def analyse(self):
        if self.part and self.fk:
            cmds.connectAttr(f'{self.mult_matrix}.matrixSum', f'{self.joint}.offsetParentMatrix', f=True)
            cmds.connectAttr(f'{self.mult_matrix}.matrixSum', f'{self.twist_matrix}.matrixIn[0]', f=True)
            q_rotate_dm = f'{self.part}QRotateDMTwist{self.side}'
            if not cmds.objExists(q_rotate_dm):
                cmds.createNode('decomposeMatrix', n=q_rotate_dm)
            cmds.connectAttr(f'{self.twist_matrix}.matrixSum', f'{q_rotate_dm}.inputMatrix', f=True)
            for axis in 'XYZ':
                qte_node = f'{self.part}QRotate{axis}QTETwist{self.side}'
                if not cmds.objExists(qte_node):
                    cmds.createNode('quatToEuler', n=qte_node)
                cmds.connectAttr(f'{q_rotate_dm}.outputQuat{axis}', f'{qte_node}.inputQuatX', f=True)
                cmds.connectAttr(f'{q_rotate_dm}.outputQuatW', f'{qte_node}.inputQuatW', f=True)
                attr = f'qRotate{axis}'
                if not cmds.objExists(f'{self.joint}.{attr}'):
                    cmds.addAttr(self.joint, ln=attr, at='double', k=True)
                cmds.connectAttr(f'{qte_node}.outputRotate{axis}', f'{self.joint}.{attr}', f=True)


class SolverSwitch(object):
    def __init__(self):
        self.__rbf_nodes = None
        self.__rig_system = None

    @property
    def rbf_nodes(self):
        if not self.__rbf_nodes:
            self.__rbf_nodes = cmds.ls(type="UERBFSolverNode")
        return self.__rbf_nodes

    @property
    def rig_system(self):
        if not self.__rig_system:
            self.__rig_system = RigSystem()
        return self.__rig_system

    def get_rbf_control_info(self, rbf_node):
        info = []
        if rbf_node in self.rbf_nodes:
            con_list = cmds.listConnections(f'{rbf_node}.outputs[0]', s=False, d=True, p=False)
            con_list.sort()
            blend_nodes = list(set(con_list))
            for blend_node in blend_nodes:
                dmt_node = cmds.listConnections(f'{blend_node}.outMatrix', s=False, d=True, p=False)
                trans = cmds.listConnections(f'{blend_node}.drivenTransform', s=False, d=True, p=False)
                if dmt_node and trans:
                    info.append(
                        {'blend_node': blend_node, 'dmt_node': dmt_node[0], 'trans': trans[0]}
                    )
        return info

    def switch_control_mode(self, rbf_node, mode=0):
        """
        # 切换控制模式
        :param rbf_node: RBF节点
        :param mode: 控制模式 0:sdk控制模式
                            1:fk控制模式
        """
        if rbf_node in self.rbf_nodes:
            name = rbf_node.replace('_UERBFSolver', '')
            self.rig_system.change_name(name)
            # 转换控制方式
            if mode == 0:
                cmds.connectAttr(f"{self.rig_system.twist_matrix}.matrixSum", f"{rbf_node}.inputs[0]", f=True)
            elif mode == 1:
                cmds.connectAttr(f"{self.rig_system.fk}.matrix", f"{rbf_node}.inputs[0]", f=True)

            rbf_info = self.get_rbf_control_info(rbf_node)
            for info in rbf_info:
                trans_node = info.get('trans')
                self.rig_system.change_name(trans_node)
                if mode == 0:
                    new_trans = self.rig_system.sdk
                elif mode == 1:
                    new_trans = self.rig_system.fk
                else:
                    new_trans = ''
                if new_trans:
                    pose_attr = f'{new_trans}.poseBlender'
                    if not cmds.objExists(pose_attr):
                        cmds.addAttr(new_trans, ln='poseBlender', at='message')
                    blend_node = info.get('blend_node')
                    dmt_node = info.get('dmt_node')
                    if blend_node and dmt_node:
                        cmds.connectAttr(f'{blend_node}.drivenTransform', pose_attr, f=True)
                        cmds.connectAttr(f'{dmt_node}.outputTranslate', f'{new_trans}.translate', f=True)
                        cmds.connectAttr(f'{dmt_node}.outputRotate', f'{new_trans}.rotate', f=True)
                        cmds.connectAttr(f'{dmt_node}.outputScale', f'{new_trans}.scale', f=True)
                    # 断掉原始transform连接
                    if trans_node != new_trans:
                        try:
                            cmds.disconnectAttr(f'{blend_node}.drivenTransform', f'{trans_node}.poseBlender')
                            cmds.disconnectAttr(f'{dmt_node}.outputTranslate', f'{trans_node}.translate')
                            cmds.disconnectAttr(f'{dmt_node}.outputRotate', f'{trans_node}.rotate')
                            cmds.disconnectAttr(f'{dmt_node}.outputScale', f'{trans_node}.scale')
                            cmds.setAttr(f'{trans_node}.t', 0, 0, 0, type='double3')
                            cmds.setAttr(f'{trans_node}.r', 0, 0, 0, type='double3')
                            cmds.setAttr(f'{trans_node}.s', 1, 1, 1, type='double3')
                        except Exception as e:
                            print(e)

    def switch_to_sdk(self, rbf_node):
        self.switch_control_mode(rbf_node, mode=0)

    def switch_to_fk(self, rbf_node):
        self.switch_control_mode(rbf_node, mode=1)

    def switch_all_to_sdk(self):
        for rbf_node in self.rbf_nodes:
            self.switch_to_sdk(rbf_node)

    def switch_all_to_fk(self):
        for rbf_node in self.rbf_nodes:
            self.switch_to_fk(rbf_node)
