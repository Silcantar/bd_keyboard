from math import sqrt
from build123d import *
from bd_keyboard.src.common import RectangleBlended
from ocp_vscode import show

r_blend = RectangleBlended(
    width=20,
    height=10,
    radius=2.5,
    tangent_scalar=(1 + sqrt(5))/2,
    rotation=45,
    align=(Align.MIN, Align.MAX)
    )

r_round = RectangleRounded(
    width=20,
    height=10,
    radius=2.5,
    rotation=45,
    align=(Align.MIN, Align.MAX)
    )

show(r_blend, r_round, r_blend - r_round)
