import typing
from dataclasses import dataclass

from build123d import *

class USB_C_Port(BasePartObject):
    """USB-C Port."""

    def __init__(
        self,
        parameters = None,
        mode: Mode = Mode.ADD,
        **kwargs
    ):
        if parameters is None:
            self.parameters = Parameters()
        else:
            self.parameters = parameters
        self.mode = mode
        p = self.parameters
        location = Location(
            position=(0, 0, p.size.Z/2),
            orientation=(90, 0, 0)
        )
        size = p.size
        radius = p.radius
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
            *size,
            align=(Align.CENTER, Align.MAX, Align.MIN)
        )
        port = fillet(
            objects=fillet_edges(port),
            radius=radius
        )
        if mode == Mode.SUBTRACT:
            cutout_location = Location(port.faces().sort_by(Axis.Y)[-1].center())
            cutout = cutout_location * Box(
                *p.cut_size,
                align=(Align.CENTER, Align.MIN, Align.CENTER)
            )
            cutout = fillet(
                objects=fillet_edges(cutout),
                radius=p.cut_radius
            )
            cutout.color = ("Yellow", 0.3)
            cutout.label = "Cutout"
            assembly = Part(children=[port, cutout])
        else:
            inside_location = Pos(0, p.size.Y - p.thickness - p.inside_depth, 0)
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
                align=(Align.CENTER, Align.MIN, Align.CENTER)
            )
            tongue = fillet(
                objects=tongue.edges().filter_by(Axis.Y),
                radius=p.tongue_radius
            )
            tongue.color = "Black"
            tongue.label = "Tongue"
            assembly = Part(children=[port, tongue])
        super().__init__(
            part=assembly,
            mode=mode,
            **kwargs
        )
        self.color = p.color
        self.label = "USB-C Port"

@dataclass
class Parameters:
    color = "Silver"
    clearance = 0.5
    cut_size = Vector(12, 100, 7)
    cut_radius = 3
    inside_depth = 6.2
    radius = 1.2
    size = Vector(9, 7.35, 3.3)
    squared = False
    thickness = 0.3
    tongue_size = Vector(6.690, 4.45, 1.2)
    tongue_radius = 0.4

if __name__ == "__main__":
    from ocp_vscode import show
    show(USB_C_Port(
        mode=Mode.SUBTRACT
    ))