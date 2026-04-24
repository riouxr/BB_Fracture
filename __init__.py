import bpy


BOOL_A_MOD = "BB_Bool_A"
BOOL_B_MOD = "BB_Bool_B"
CUTTER_NAMES = ("BoolA", "BoolB")


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def find_layer_collection(layer_coll, name):
    if layer_coll.collection.name == name:
        return layer_coll
    for child in layer_coll.children:
        result = find_layer_collection(child, name)
        if result:
            return result
    return None


def has_mod(obj, name):
    return any(m.name == name for m in obj.modifiers)


def get_a_objects():
    return [
        o for o in bpy.data.objects
        if o.type == 'MESH'
        and (o.get("bb_fracture_side") == "A" or has_mod(o, BOOL_A_MOD))
    ]


def get_b_objects():
    return [
        o for o in bpy.data.objects
        if o.type == 'MESH'
        and (o.get("bb_fracture_side") == "B" or has_mod(o, BOOL_B_MOD))
    ]


def safe_hide(obj, state):
    try:
        obj.hide_set(state)
    except RuntimeError:
        # Object not in current view layer (e.g. excluded collection) - skip
        pass


def update_display(scene):
    """Apply the current display mode to all _A / _B objects."""
    mode = scene.bb_fracture_display_mode
    for o in get_a_objects():
        safe_hide(o, mode == 'B')
    for o in get_b_objects():
        safe_hide(o, mode == 'A')
    if mode in ('A', 'B'):
        for name in CUTTER_NAMES:
            c = bpy.data.objects.get(name)
            if c:
                safe_hide(c, False)


# -----------------------------------------------------------------------------
# Operators
# -----------------------------------------------------------------------------

class BB_OT_fracture(bpy.types.Operator):
    bl_idname = "bb_fracture.fracture"
    bl_label = "Fracture"
    bl_description = "Create _A and _B boolean copies using BoolA and BoolB as cutters"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.selected_objects
            and "BoolA" in bpy.data.objects
            and "BoolB" in bpy.data.objects
        )

    def execute(self, context):
        bool_a = bpy.data.objects.get("BoolA")
        bool_b = bpy.data.objects.get("BoolB")

        if not bool_a or not bool_b:
            self.report({'ERROR'}, "BoolA and/or BoolB not found in scene")
            return {'CANCELLED'}

        selected = [
            obj for obj in context.selected_objects
            if obj.type == 'MESH' and obj.name not in CUTTER_NAMES
        ]

        if not selected:
            self.report({'ERROR'}, "No valid mesh objects selected")
            return {'CANCELLED'}

        orig_collection = bpy.data.collections.get("Orig")
        if not orig_collection:
            orig_collection = bpy.data.collections.new("Orig")
            context.scene.collection.children.link(orig_collection)

        new_objects = []

        for obj in selected:
            original_collections = list(obj.users_collection)

            # Copy A
            obj_a = obj.copy()
            obj_a.data = obj.data.copy()
            obj_a.name = f"{obj.name}_A"
            for coll in original_collections:
                if coll.name != "Orig":
                    coll.objects.link(obj_a)
            mod_a = obj_a.modifiers.new(name=BOOL_A_MOD, type='BOOLEAN')
            mod_a.operation = 'DIFFERENCE'
            mod_a.solver = 'EXACT'
            mod_a.use_hole_tolerant = True
            mod_a.object = bool_a
            obj_a["bb_fracture_side"] = "A"

            # Copy B
            obj_b = obj.copy()
            obj_b.data = obj.data.copy()
            obj_b.name = f"{obj.name}_B"
            for coll in original_collections:
                if coll.name != "Orig":
                    coll.objects.link(obj_b)
            mod_b = obj_b.modifiers.new(name=BOOL_B_MOD, type='BOOLEAN')
            mod_b.operation = 'DIFFERENCE'
            mod_b.solver = 'EXACT'
            mod_b.use_hole_tolerant = True
            mod_b.object = bool_b
            obj_b["bb_fracture_side"] = "B"

            # Move original to "Orig" collection
            for coll in original_collections:
                coll.objects.unlink(obj)
            if obj.name not in orig_collection.objects:
                orig_collection.objects.link(obj)

            new_objects.extend([obj_a, obj_b])

        layer_coll = find_layer_collection(context.view_layer.layer_collection, "Orig")
        if layer_coll:
            layer_coll.hide_viewport = True

        bpy.ops.object.select_all(action='DESELECT')
        for obj in new_objects:
            obj.select_set(True)
        if new_objects:
            context.view_layer.objects.active = new_objects[0]

        self.report({'INFO'}, f"Fractured {len(selected)} object(s)")
        return {'FINISHED'}


class BB_OT_display_a(bpy.types.Operator):
    bl_idname = "bb_fracture.display_a"
    bl_label = "Display A"
    bl_description = "Toggle: show only _A objects and the BoolA/BoolB cutters"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        scene.bb_fracture_display_mode = 'NONE' if scene.bb_fracture_display_mode == 'A' else 'A'
        update_display(scene)
        return {'FINISHED'}


class BB_OT_display_b(bpy.types.Operator):
    bl_idname = "bb_fracture.display_b"
    bl_label = "Display B"
    bl_description = "Toggle: show only _B objects and the BoolA/BoolB cutters"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        scene.bb_fracture_display_mode = 'NONE' if scene.bb_fracture_display_mode == 'B' else 'B'
        update_display(scene)
        return {'FINISHED'}


class BB_OT_apply(bpy.types.Operator):
    bl_idname = "bb_fracture.apply"
    bl_label = "Apply"
    bl_description = "Apply BB boolean modifiers on the selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        applied = 0
        previous_active = context.view_layer.objects.active

        for obj in list(context.selected_objects):
            if obj.type != 'MESH':
                continue
            context.view_layer.objects.active = obj
            for mod in list(obj.modifiers):
                if mod.name in (BOOL_A_MOD, BOOL_B_MOD):
                    try:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                        applied += 1
                    except RuntimeError as e:
                        self.report({'WARNING'}, f"{obj.name}: {e}")

        if previous_active:
            context.view_layer.objects.active = previous_active

        self.report({'INFO'}, f"Applied {applied} modifier(s)")
        return {'FINISHED'}


class BB_OT_apply_all(bpy.types.Operator):
    bl_idname = "bb_fracture.apply_all"
    bl_label = "Apply All"
    bl_description = "Apply BB boolean modifiers on all _A and _B objects in the scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        targets = list(dict.fromkeys(get_a_objects() + get_b_objects()))
        if not targets:
            self.report({'WARNING'}, "No _A or _B objects found")
            return {'CANCELLED'}

        applied = 0
        previous_active = context.view_layer.objects.active

        for obj in targets:
            context.view_layer.objects.active = obj
            for mod in list(obj.modifiers):
                if mod.name in (BOOL_A_MOD, BOOL_B_MOD):
                    try:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                        applied += 1
                    except RuntimeError as e:
                        self.report({'WARNING'}, f"{obj.name}: {e}")

        if previous_active:
            context.view_layer.objects.active = previous_active

        self.report({'INFO'}, f"Applied {applied} modifier(s)")
        return {'FINISHED'}


# -----------------------------------------------------------------------------
# Panel
# -----------------------------------------------------------------------------

class BB_PT_fracture_panel(bpy.types.Panel):
    bl_label = "BB Fracture"
    bl_idname = "BB_PT_fracture"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout

        bool_a_exists = "BoolA" in bpy.data.objects
        bool_b_exists = "BoolB" in bpy.data.objects

        box = layout.box()
        box.label(text="Cutters in scene:")
        row = box.row()
        row.label(text="BoolA", icon='CHECKMARK' if bool_a_exists else 'ERROR')
        row = box.row()
        row.label(text="BoolB", icon='CHECKMARK' if bool_b_exists else 'ERROR')

        layout.separator()
        col = layout.column()
        col.scale_y = 1.4
        col.operator("bb_fracture.fracture", text="Fracture", icon='MOD_BOOLEAN')

        layout.separator()
        layout.label(text="Display:")
        mode = context.scene.bb_fracture_display_mode
        row = layout.row(align=True)
        row.operator("bb_fracture.display_a", text="Display A", depress=(mode == 'A'))
        row.operator("bb_fracture.display_b", text="Display B", depress=(mode == 'B'))

        layout.separator()
        layout.label(text="Apply:")
        row = layout.row(align=True)
        row.operator("bb_fracture.apply", text="Apply")
        row.operator("bb_fracture.apply_all", text="Apply All")


# -----------------------------------------------------------------------------
# Registration
# -----------------------------------------------------------------------------

classes = (
    BB_OT_fracture,
    BB_OT_display_a,
    BB_OT_display_b,
    BB_OT_apply,
    BB_OT_apply_all,
    BB_PT_fracture_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.bb_fracture_display_mode = bpy.props.EnumProperty(
        name="BB Fracture Display Mode",
        items=[
            ('NONE', "None", "Show everything"),
            ('A', "A", "Show only A objects"),
            ('B', "B", "Show only B objects"),
        ],
        default='NONE',
    )


def unregister():
    del bpy.types.Scene.bb_fracture_display_mode
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
