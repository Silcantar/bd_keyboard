from dataclasses import dataclass
from enum import StrEnum

from build123d import *

try:
    from bd_keyboard.src.common import *
except ImportError:
    from common import *

class Style(StrEnum):
    RECTANGULAR = auto()
    ROUND = auto()
    ROTATABLE = auto()

class Side(StrEnum):
    PAD = auto()
    PIN = auto()

@dataclass
class MagneticConnectorParameters:
    body_color: ColorLike = 0x202020
    body_size: vector[3] = (16.5, 4.0, 4.7)
    boss_angle: float = 15
    boss_radius: float = 0.5
    boss_size: vector[2] = (2.0, 3.0)
    fillet_radius: float = 0.1
    header_size: vector[2] = (0.5, 2.0)
    lip_size: vector[2] = (1.0, 1.0)
    lip_position: float = 1.0
    magnet_color: ColorLike = "Silver"
    magnet_height: float = 3
    magnet_radius: float = 0.2
    magnet_wall_thickness: float = 0.5
    pad_radius: float = 0.75
    pin_color: ColorLike = "DarkGoldenRod"
    pin_size: vector[2] = (0.5, 1.0)
    pitch: float = 2.0

class MagneticConnector(Part):
    """Model a variety of styles of magnetic pogo-pin connectors."""

    def __init__(
        self,
        side: Side,
        style: Style = Style.RECTANGULAR,
        parameters: MagneticConnectorParameters = MagneticConnectorParameters(),
        rows: int = 1,
        columns: int = 4,
        row_offsets: list[float] = None,
        label: str = "Magnetic Connector",
        **kwargs
        ):
        self.side = side
        self.parameters = parameters
        self.columns = columns
        self.rows = rows
        if row_offsets is None:
            self.row_offsets = [0] * rows
        else:
            self.row_offsets = row_offsets
        match style:
            case Style.RECTANGULAR:
                components = self.connector_rectangular()
            case Style.ROUND:
                components = self.connector_round()
            case Style.ROTATABLE:
                components = self.connector_rotatable()
        super().__init__(
            children=components,
            label=label,
            **kwargs
            )

    def connector_rectangular(self) -> list[Part]:
        """Model a magnetic pogo-pin connector with a configurable rectangular
        array of pins.
        """
        p = self.parameters
        pin_locations = [
            Pos(
                (i - self.columns/2 + 0.5 + self.row_offsets[j])*p.pitch,
                (j - self.rows/2 + 0.5)*p.pitch
                )
            for j in range(self.rows)
            for i in range(self.columns)
            ]
        if self.side == Side.PAD:
            pins = pin_locations * self.pad()
        else:
            pins = pin_locations * self.pin()
        self.width = p.pitch*(self.columns-1) + p.body_size[X]
        self._depth = p.pitch*(self.rows-1) + p.body_size[Y]
        self.radius = self._depth/2
        body_sketch = RectangleRounded(
            self.width,
            self._depth,
            self.radius
            )
        body = extrude(
            body_sketch,
            amount=-p.body_size[Z]
            )
        lip_sketch = (
            Pos(Z=-p.lip_position)
            * RectangleRounded(
                self.width + 2*p.lip_size[R],
                self._depth + 2*p.lip_size[R],
                self.radius + p.lip_size[R]
                )
            )
        body += extrude(lip_sketch, amount=-p.lip_size[H])
        boss_sketch = Trapezoid(
            (
                p.boss_size[X]
                + p.pitch*(self.columns-1)
                + 2*(p.pitch + p.boss_size[Y])*tand(p.boss_angle)
                ),
            p.boss_size[Y] + p.pitch*(self.rows-1),
            left_side_angle=90-p.boss_angle
            )
        boss_sketch = fillet(
            boss_sketch.vertices(),
            radius=p.boss_radius
            )
        if self.side == Side.PAD:
            body += extrude(boss_sketch, amount=p.pin_size[H])
        else:
            body -= extrude(boss_sketch, amount=-p.pin_size[H])
        magnet_locations = [
            Location(
                position=(
                    i*(self.width/2 - p.magnet_wall_thickness),
                    0,
                    -p.body_size[Z]
                    ),
                orientation=(0, 0, -90*i)
                )
            for i in (-1, 1)
            ]
        magnets = magnet_locations * self.magnet()
        body -= pins
        body -= magnet_locations * self.magnet(round=False)
        if p.fillet_radius > 0:
            body = fillet(body.edges(), radius=p.fillet_radius)
        body.color = p.body_color
        body.label = "Body"
        return [body, *pins, *magnets]

    def connector_round(self) -> list[Part]:
        """Model a non-rotatable round magnetic pogo-pin connector with a
        configurable number of pins.
        """
        raise NotImplementedError()

    def connector_rotatable(self) -> list[Part]:
        """Model a rotatable round magnetic pogo-pin connector with a
        configurable number of pins.
        """
        raise NotImplementedError()

    def pad(self) -> Part:
        p = self.parameters
        pad = (
            Pos(Z=p.pin_size[H])
            * Cylinder(
                p.pad_radius,
                p.body_size[Z] + p.pin_size[H],
                align=TOP
                )
            )
        pad += (
            pad.faces().sort_by(Axis.Z)[0].center_location
            * Cylinder(*p.header_size, align=BOTTOM)
            )
        pad.color = p.pin_color
        pad.label = "Pad"
        return pad

    def pin(self) -> Part:
        p = self.parameters
        pin = Cylinder(*p.pin_size, align=TOP)
        pin += (
            pin.faces().sort_by(Axis.Z)[0].center_location
            * Cylinder(
                p.pad_radius,
                p.body_size[Z] - p.pin_size[H],
                align=BOTTOM
                )
            )
        pin += (
            pin.faces().sort_by(Axis.Z)[0].center_location
            * Cylinder(*p.header_size, align=BOTTOM)
            )
        pin = fillet(
            pin.edges().sort_by(Axis.Z)[-1],
            radius=p.pin_size[R] - EPS
            )
        pin.color = p.pin_color
        pin.label = "Pin"
        return pin

    def magnet(self, round: bool = True) -> Part:
        p = self.parameters
        width = self._depth-2*p.magnet_wall_thickness
        magnet_sketch = RectangleRounded(
            width, width,
            radius=[0, width/2, width/2, 0],
            align=BACK_BOTTOM
            )
        magnet = extrude(magnet_sketch, amount=p.magnet_height)
        if round:
            magnet = fillet(magnet.edges(), radius=p.magnet_radius)
        magnet.color = p.magnet_color
        magnet.label = "Magnet"
        return magnet


# class MagneticConnectorRound(Part):

#     def __init__(self):
#         raise NotImplementedError()

# class MagneticConnectorRotatable(Part):

#     def __init__(self):
#         raise NotImplementedError()

if __name__ == "__main__":
    from ocp_vscode import show
    show(
        (
            Pos(Y=-20)
            * MagneticConnector(
                side=Side.PAD,
                columns=6,
                rows=2
                )
            ),
        (
            Pos(Y=20)
            * MagneticConnector(
                side=Side.PIN,
                columns=6,
                rows=2
                )
            )
        )