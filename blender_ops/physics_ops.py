# blender_ops/physics_ops.py
"""
MMD physics setup: rigid bodies and joints for hair/cloth dynamics.
"""
import bpy
from mathutils import Vector
from .utils import find_aimm_object, find_all_aimm_objects


def setup_hair_physics(stiffness: float = 0.5, damping: float = 0.3):
    """
    Create rigid body chain for hair physics.
    Uses a chain of rigid bodies connected by spring joints along the hair strands.

    Args:
        stiffness: 0-1 joint stiffness
        damping: 0-1 joint damping
    """
    hair = find_aimm_object("hair")
    if hair is None:
        return 0, 0

    # Create physics root (kinematic body anchored to head)
    head_z = hair.location.z + 0.12  # Approximate head center

    rigid_bodies = 0
    joints = 0

    # Create a chain of rigid bodies along the vertical extent of hair
    chain_count = 5
    chain_spacing = 0.06

    for side in range(2):  # Left and right
        x_offset = (side - 0.5) * 0.15
        prev_body = None

        for i in range(chain_count):
            z = head_z - (i + 1) * chain_spacing

            # Create empty for rigid body
            bpy.ops.object.empty_add(type='SPHERE', radius=0.015, location=(x_offset, 0, z))
            rb_obj = bpy.context.active_object
            rb_obj.name = f"AIMoeMaker_HairRB_{side}_{i}"
            rb_obj["aimm_type"] = "physics_hair"

            # Add rigid body
            bpy.ops.rigidbody.object_add()
            rb = rb_obj.rigid_body

            if i == 0:
                rb.type = 'PASSIVE'  # First body is kinematic (attached to head)
                rb.kinematic = True
            else:
                rb.type = 'ACTIVE'
                rb.mass = 0.1
                rb.linear_damping = damping
                rb.angular_damping = damping * 0.5

            rigid_bodies += 1

            # Create joint to previous body
            if prev_body is not None:
                bpy.ops.object.empty_add(type='ARROWS', radius=0.01, location=(x_offset, 0, z + chain_spacing * 0.5))
                joint_obj = bpy.context.active_object
                joint_obj.name = f"AIMoeMaker_HairJoint_{side}_{i}"
                joint_obj["aimm_type"] = "physics_hair"

                bpy.ops.rigidbody.constraint_add()
                joint = joint_obj.rigid_body_constraint
                joint.type = 'GENERIC_SPRING'
                joint.object1 = prev_body
                joint.object2 = rb_obj

                # Spring settings based on stiffness
                spring_stiffness = stiffness * 50
                joint.use_spring_x = True
                joint.use_spring_y = True
                joint.use_spring_z = True
                joint.spring_stiffness_x = spring_stiffness
                joint.spring_stiffness_y = spring_stiffness
                joint.spring_stiffness_z = spring_stiffness
                joint.spring_damping_x = damping * 10
                joint.spring_damping_y = damping * 10
                joint.spring_damping_z = damping * 10

                # Limit rotation
                joint.use_limit_ang_x = True
                joint.use_limit_ang_y = True
                joint.use_limit_ang_z = True
                joint.limit_ang_x_lower = -0.5
                joint.limit_ang_x_upper = 0.5
                joint.limit_ang_y_lower = -0.3
                joint.limit_ang_y_upper = 0.3
                joint.limit_ang_z_lower = -0.5
                joint.limit_ang_z_upper = 0.5

                joints += 1

            prev_body = rb_obj

    return rigid_bodies, joints


def setup_cloth_physics(clothing_index: int = 0):
    """
    Add cloth physics simulation to a clothing mesh.
    This uses Blender's cloth modifier rather than rigid bodies.
    """
    # Find clothing objects (they would be tagged with aimm_type="clothing")
    clothing_objs = find_all_aimm_objects("clothing")
    if clothing_index >= len(clothing_objs):
        return False

    cloth_obj = clothing_objs[clothing_index]

    # Add cloth modifier if not present
    if "Cloth" not in [m.name for m in cloth_obj.modifiers]:
        mod = cloth_obj.modifiers.new("Cloth", 'CLOTH')
        cloth = mod.settings
        cloth.quality = 5
        cloth.mass = 0.3
        cloth.air_damping = 1.0

        # Pin group (vertices near waist should be pinned)
        # For now, use default settings

    return True
