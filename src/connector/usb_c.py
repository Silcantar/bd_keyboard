import typing
from dataclasses import dataclass

from build123d import *

try:
    from bd_keyboard.src.common import *
except ImportError:
    from common import *

@dataclass
class USB_C_Parameters:
    color: ColorLike = "Silver"
    clearance: float = 0.5
    cut_size: vector[3] = (12, 100, 7)
    cut_radius: float = 3
    inside_depth: float = 6.2
    radius: float = 1.2
    size: vector[3] = (9, 7.35, 3.3)
    squared: bool = False
    thickness: float = 0.3
    tongue_size: vector[3] = (6.690, 4.45, 1.2)
    tongue_radius: float = 0.4

class USB_C_Port(Part):
    """USB-C Port."""

    def __init__(
        self,
        parameters: USB_C_Parameters = USB_C_Parameters(),
        mode: Mode = Mode.ADD,
        label: str = "USB-C Port",
        **kwargs
    ):
        self.parameters = parameters
        self.mode = mode
        p = self.parameters
        location = Location(
            position=(0, 0, p.size[Z]/2),
            orientation=(90, 0, 0)
        )
        fillet_edges = lambda p: p.edges().filter_by(Axis.Y)
        if mode == Mode.SUBTRACT:
            size = p.size + (2*p.clearance, 0, 2*p.clearance)
            radius = p.radius + p.clearance
            if p.squared:
                fillet_edges = (
                    lambda p:
                    p.edges()
                    .filter_by(Axis.Y)
                    .group_by(Axis.Z)[-1]
                )
        port = Box(
            *p.size,
            align=BACK_BOTTOM
        )
        port = fillet(
            objects=fillet_edges(port),
            radius=p.radius
        )
        if mode == Mode.SUBTRACT:
            cutout_location = Location(port.faces().sort_by(Axis.Y)[-1].center())
            cutout = cutout_location * Box(
                *p.cut_size,
                align=FRONT
            )
            cutout = fillet(
                objects=fillet_edges(cutout),
                radius=p.cut_radius
            )
            cutout.color = ("Yellow", 0.3)
            cutout.label = "Cutout"
            assembly = Part(children=[port, cutout])
        else:
            inside_location = Pos(
                0,
                p.size[Y] - p.thickness - p.inside_depth,
                0
                )
            inside = inside_location * offset(
                objects=port,
                amount=-p.thickness
            )
            port -= inside
            tongue_location = Location(
                port.faces()
                .filter_by(Axis.Y)
                .sort_by(Axis.Y)[1]
                .center()
            )
            tongue = tongue_location * Box(
                *p.tongue_size,
                align=FRONT
            )
            tongue = fillet(
                objects=tongue.edges().filter_by(Axis.Y),
                radius=p.tongue_radius
            )
            tongue.color = "Black"
            tongue.label = "Tongue"
            assembly = Part(children=[port, tongue])
        super().__init__(
            obj=assembly,
            label=label,
            color=p.color,
            **kwargs
            )
        RigidJoint(
            label="pcb",
            to_part=self,
            joint_location=Pos(
                port.edges()
                .group_by(Axis.Z)[0]
                .sort_by(Axis.Y)[-1]
                .center()
                )
            )
        RigidJoint(
            label="plug",
            to_part=self,
            joint_location=Pos(port.faces().sort_by(Axis.Y)[-1].center())
            )

if __name__ == "__main__":
    from ocp_vscode import show
    show(
        USB_C_Port(
            # mode=Mode.SUBTRACT
            ),
        render_joints=True
        )