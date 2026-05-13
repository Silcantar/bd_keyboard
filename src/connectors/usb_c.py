import typing
from dataclasses import dataclass

from build123d import *

class USB_C_Port(BasePartObject):
    """USB-C Port."""

    def __init__(
        self,
        parameters: Parameters = None,
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
        port_sketch = RectangleRounded(
            width=p.size.X,
            height=p.size.Z,
            radius=1.2
        )
        port = location * extrude(
            to_extrude=port_sketch,
            amount=p.size.Y
        )
        if mode == Mode.SUBTRACT:
            cutout_sketch = RectangleRounded(
                width=p.cut_size.X,
                height=p.cut_size.Z,
                radius=p.cut_radius
            )
            cutout = location * extrude(
                to_extrude=cutout_sketch,
                amount=-p.cut_size.Y
            )
            cutout.color = ("Yellow", 0.3)
            cutout.label = "Cutout"
            assembly = Part(children=[port, cutout])
        else:
            inside_location = Pos(0, p.size.Y - p.inside_depth, 0)
            inside = inside_location * offset(
                objects=port,
                amount=-p.thickness
            )
            port -= inside
            tongue_locations = Locations(
                port.faces()
                .filter_by(Axis.Y)
                .sort_by(Axis.Y)[1]
            )
            tongue_sketch = RectangleRounded(
                width=p.tongue_size.X,
                height=p.tongue_size.Z,
                radius=p.tongue_radius
            )
            tongue = tongue_locations.locations[0] * extrude(
                to_extrude=tongue_sketch,
                amount=p.tongue_size.Y
            )
            tongue.color = "Black"
            tongue.label = "Tongue"
            # port += tongue
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
    cut_size = Vector(12, 10, 7)
    cut_radius = 3
    inside_depth = 6.2
    radius = 1.2
    size = Vector(9, 7.35, 3.3)
    thickness = 0.3
    tongue_size = Vector(6.690, 4.45, 1.2)
    tongue_radius = 0.4

if __name__ == "__main__":
    from ocp_vscode import show
    show(USB_C_Port(
        # mode=Mode.SUBTRACT
    ))