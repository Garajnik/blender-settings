import bpy
import operator
from mathutils import Vector

from . import settings

frame_range = 50



class op(bpy.types.Operator):
	bl_idname = "uv.textools_bake_explode"
	bl_label = "Explode"
	bl_description = "Explode selected bake pairs with animation keyframes"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if len(settings.sets) <= 1:
			return False
		return True


	def execute(self, context):
		explode(self)
		return {'FINISHED'}



def explode(self):
	sets = settings.sets

	set_bounds = {}
	set_volume = {}
	avg_side = 0
	for bset in sets:
		set_bounds[bset] = get_bbox_set(bset)
		set_volume[bset] = set_bounds[bset]['size'].x * set_bounds[bset]['size'].y * set_bounds[bset]['size'].z

		avg_side+=set_bounds[bset]['size'].x
		avg_side+=set_bounds[bset]['size'].y
		avg_side+=set_bounds[bset]['size'].z

	avg_side/=(len(sets)*3)

	sorted_set_volume = sorted(set_volume.items(), key=operator.itemgetter(1))
	sorted_sets = [item[0] for item in sorted_set_volume]
	sorted_sets.reverse()

	# All combined bounding boxes
	bbox_all = merge_bounds(list(set_bounds.values()))
	bbox_max = set_bounds[ sorted_sets[0] ] #  max_bbox(list(set_bounds.values()))

	# Offset sets into their direction
	dir_offset_last_bbox = {}
	for i in range(0,6):
		dir_offset_last_bbox[i] = bbox_max #bbox_all

	bpy.context.scene.frame_start = 0
	bpy.context.scene.frame_end = frame_range
	bpy.context.scene.frame_current = 0
	
	# Process each set
	for bset in sorted_sets[1:]:
		#if set_bounds[bset] != bbox_max:
		delta = set_bounds[bset]['center'] - bbox_all['center']
		offset_set(bset, delta, avg_side*0.35, dir_offset_last_bbox)

	bpy.context.scene.frame_current = frame_range



def offset_set(bset, delta, margin, dir_offset_last_bbox):
	objects = bset.objects_low + bset.objects_high + bset.objects_cage

	# Which Direction?
	delta_max = max(abs(delta.x), abs(delta.y), abs(delta.z))
	direction = [0,0,0]
	if delta_max > 0:
		for i in range(0,3):
			if abs(delta[i]) == delta_max:
				direction[i] = delta[i]/abs(delta[i])
				break
			else:
				direction[i] = 0
	else:
		# When no delta offset is measured, move up
		direction = [0,0,1]

	delta = Vector((direction[0], direction[1], direction[2]))

	# Get Key
	key = get_delta_key(delta)

	# Calculate Offset
	bbox = get_bbox_set(bset)
	bbox_last = dir_offset_last_bbox[key]
	
	offset = Vector((0,0,0))

	if delta.x == 1:
		offset = delta * ( bbox_last['max'].x - bbox['min'].x )
	elif delta.x == -1:
		offset = delta * -( bbox_last['min'].x - bbox['max'].x )
	
	elif delta.y == 1:
		offset = delta * ( bbox_last['max'].y - bbox['min'].y )
	elif delta.y == -1:
		offset = delta * -( bbox_last['min'].y - bbox['max'].y )
	
	elif delta.z == 1:
		offset = delta * ( bbox_last['max'].z - bbox['min'].z )
	elif delta.z == -1:
		offset = delta * -( bbox_last['min'].z - bbox['max'].z )

	# Add margin
	offset += delta * margin

	for obj in objects:
		bpy.context.view_layer.update()
		obj.keyframe_insert(data_path="location", frame=0)
		obj.location += offset
		bpy.context.view_layer.update()
		obj.keyframe_insert(data_path="location", frame=frame_range)

	# Update last bbox in direction
	dir_offset_last_bbox[key] = get_bbox_set(bset)



def get_delta_key(delta):
	if delta.x == -1:
		return 0
	elif delta.x == 1:
		return 1
	if delta.y == -1:
		return 2
	elif delta.y == 1:
		return 3
	if delta.z == -1:
		return 4
	elif delta.z == 1:
		return 5



def merge_bounds(bounds):
	box_min = bounds[0]['min'].copy()
	box_max = bounds[0]['max'].copy()
	
	for bbox in bounds:
		box_min.x = min(box_min.x, bbox['min'].x)
		box_min.y = min(box_min.y, bbox['min'].y)
		box_min.z = min(box_min.z, bbox['min'].z)
		
		box_max.x = max(box_max.x, bbox['max'].x)
		box_max.y = max(box_max.y, bbox['max'].y)
		box_max.z = max(box_max.z, bbox['max'].z)

	return {
		'min':box_min, 
		'max':box_max, 
		'size':(box_max-box_min),
		'center':box_min+(box_max-box_min)/2
	}



def get_bbox_set(bset):
	objects = bset.objects_low + bset.objects_high + bset.objects_cage
	bounds = []
	for obj in objects:
		bounds.append( get_bbox(obj) )
	return merge_bounds(bounds)



def get_bbox(obj):
	corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

	# Get world space Min / Max
	box_min = Vector((corners[0].x, corners[0].y, corners[0].z))
	box_max = Vector((corners[0].x, corners[0].y, corners[0].z))
	for corner in corners:
		# box_min.x = -8
		box_min.x = min(box_min.x, corner.x)
		box_min.y = min(box_min.y, corner.y)
		box_min.z = min(box_min.z, corner.z)
		
		box_max.x = max(box_max.x, corner.x)
		box_max.y = max(box_max.y, corner.y)
		box_max.z = max(box_max.z, corner.z)

	return {
		'min':box_min, 
		'max':box_max, 
		'size':(box_max-box_min),
		'center':box_min+(box_max-box_min)/2
	}


bpy.utils.register_class(op)
