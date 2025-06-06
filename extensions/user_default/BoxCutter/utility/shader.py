import numpy

import bpy

from math import pi, cos, sin
from mathutils import Matrix

import gpu
from gpu.types import GPUBatch, GPUIndexBuf, GPUVertBuf
from gpu_extras.batch import batch_for_shader


def batch(shader, type, property={}, vbo_index=0, indices=[]):
    return batch_for_shader(shader, type, property, indices=indices if len(indices) else None)
    # vbo = None
    # vbo_length = 0
    # ibo = None

    # if property:
    #     vbo_length = len(list(property.values())[vbo_index])

    # vbo = GPUVertBuf(shader.format_calc(), vbo_length)

    # if property:
    #     for prop, data in property.items():
    #         vbo.attr_fill(prop, data)

    # if len(indices):
    #     ibo = GPUIndexBuf(type=type, seq=indices)
    #     return GPUBatch(type=type, buf=vbo, elem=ibo)

    # return GPUBatch(type=type, buf=vbo)


def circle_coordinates(x, y, size=10, resolution=32):
    step = lambda i: i * pi * 2 * (1 / resolution)

    vert = [(x + cos(step(i)) * size, y + sin(step(i)) * size) for i in range(resolution)]
    vert.insert(0, (x, y))

    loop_index = [(0, i + 1, i + 2 if i + 2 < resolution else 1)
                   for i in range(resolution - 1)]

    edge_vert = vert[1:]
    edge_vert.append(edge_vert[-1])

    edge_index = [(i if i < resolution else 0, i + 1 if i < resolution else resolution) for i in range(resolution + 1)]

    return vert, loop_index, edge_vert, edge_index

