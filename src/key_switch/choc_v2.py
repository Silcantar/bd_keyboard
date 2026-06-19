import typing
from dataclasses import dataclass

from build123d import *

try:
    from bd_keyboard.src.common import *
except ImportError:
    from common import *

class ChocV2(BasePartObject):
    """Kailh Choc V2 (CPG1353) key switch."""

    def __init__(
        self,
        travel: float = 0,
        upper_color: ColorLike = ("White", 0.3),
        lower_color: ColorLike = ("Black", 1.0),
        stem_color: ColorLike = ("Red", 1.0),
        **kwargs
    ):
        self.parameters = Parameters()
        switch = Part(children=[
                self._lower(
                    label="Lower",
                    color=lower_color
                ),
                Pos(Z=-travel) * self._stem(
                    label="Stem",
                    color=stem_color
                ),
                self._upper(
                    label="Upper",
                    color=upper_color
                ),
                self._contacts(
                    label="Contact",
                    color=["Silver", "DarkGoldenrod", "Silver"]
                )
        ])
        super().__init__(
            part=switch,
            **kwargs
        )

    def _contacts(self, label: str, color: list[ColorLike]) -> Part:
        p = self.parameters
        contact = Box(
            length=p.contact.size.X,
            width=p.contact.size.Y,
            height=p.contact.size.Z,
            align=(Align.CENTER, Align.CENTER, Align.MAX)
        )
        if p.contact.chamfer.length > 0:
            contact = chamfer(
                objects=(
                    contact.edges()
                    .group_by(Axis.Z)[0]
                    .group_by(SortBy.LENGTH)[0]
                ),
                length=p.contact.chamfer.X,
                length2=p.contact.chamfer.Y
            )
        contact_locs = Locations([
            Location(
                position=p.contact.position[i] + (0, 0, -p.lower.size.Z),
                # orientation=(0, 0, 90*i)
            ) for i in range(len(p.contact.position))
        ])
        contacts = Part(children=contact_locs * contact)
        contacts.label = f"{label}s"
        for i in range(len(contacts.children)):
            contacts.children[i].label = f"{label} {i+1}"
            contacts.children[i].color = color[i]
        return contacts

    def _lower(self, label: str, color: ColorLike) -> Part:
        p = self.parameters
        sketch = RectangleRounded(
            width=p.lower.size.X,
            height=p.lower.size.Y,
            radius=p.lower.corner_radius
        )
        lower = extrude(
            to_extrude=sketch,
            amount=-p.lower.size.Z,
        )
        lower = fillet(
            objects=lower.edges().group_by(Axis.Z)[0],
            radius=p.lower.fillet_radius
        )
        lip_sketch = RectangleRounded(
            width=p.lower.lip_size.X,
            height=p.lower.lip_size.Y,
            radius=p.lower.corner_radius
        )
        lip = extrude(
            to_extrude=lip_sketch,
            amount=p.lower.lip_size.Z
        )
        lip_filleted = fillet(
            objects=lip.edges().group_by(Axis.Z)[-1],
            radius=p.lower.lip_radius
        )
        lower += lip_filleted
        lower -= Pos(p.lower.cutout_position) * Box(
            length=p.lower.cutout_size.X,
            width=p.lower.cutout_size.Y,
            height=BIG,
        )
        lower -= Pos(0, 0, -p.lower.size.Z + p.lower.thickness)*Box(
            length=p.lower.size.X - 2*p.lower.thickness,
            width=p.lower.size.Y - 2*p.lower.thickness,
            height=BIG,
            align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        center_pin_loc = Pos(
            lower.faces()
            .sort_by(Axis.Z)[0]
            .bounding_box()
            .center()
            + p.center_pin.position
        )
        center_pin = center_pin_loc * Cylinder(
            radius=p.center_pin.size.X/2,
            height=p.center_pin.size.Z,
            align=(Align.CENTER, Align.CENTER, Align.MAX)
        )
        if p.center_pin.chamfer.length > 0:
            center_pin = chamfer(
                objects=center_pin.edges().sort_by(Axis.Z)[0],
                length=p.center_pin.chamfer.X,
                length2=p.center_pin.chamfer.Y
            )
        lower += center_pin
        # alignment_pin_loc = Pos(
        #     p.alignment_pin.position
        #     + (0, 0, -p.lower.size.Z)
        # )
        # alignment_pin = alignment_pin_loc * Box(
        #     length=p.alignment_pin.size.X,
        #     width=p.alignment_pin.size.Y,
        #     height=p.alignment_pin.size.Z,
        #     align=(Align.CENTER, Align.CENTER, Align.MAX)
        # )
        # if p.alignment_pin.chamfer.length > 0:
        #     alignment_pin = chamfer(
        #         objects=alignment_pin.edges().group_by(Axis.Z)[0],
        #         length=p.alignment_pin.chamfer.X,
        #         length2=p.alignment_pin.chamfer.Y
        #     )
        # lower += alignment_pin
        lower.label = label
        lower.color = color
        return lower

    def _stem(self, label: str, color: ColorLike) -> Part:
        p = self.parameters
        stem = Cylinder(
            radius=p.stem.outer_diameter/2,
            height=p.stem.height,
            align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        stem -= Location(stem.faces().sort_by(Axis.Z)[-1].center())*Cylinder(
            radius=p.stem.inner_diameter/2,
            height=p.stem.tenon_size.Z,
            align=(Align.CENTER, Align.CENTER, Align.MAX)
        )
        tenon = Part(
            Locations([
                Location(
                    position=stem.faces().sort_by(Axis.Z)[-1].center(),
                    orientation=(0, 0, z)
                )
                for z in [0, 90]
            ])
            * Box(
                length=p.stem.tenon_size.X,
                width=p.stem.tenon_size.Y,
                height=p.stem.tenon_size.Z,
                align=(Align.CENTER, Align.CENTER, Align.MAX)
            )
        )
        tenon = chamfer(
            objects=tenon.faces().group_by(Axis.Z)[-1].edges(),
            length=0.2
        )
        stem += tenon
        stem.label = label
        stem.color = color
        return stem

    def _upper(self, label: str, color: ColorLike) -> Part:
        p = self.parameters
        upper = Box(
            length=p.upper.size.X,
            width=p.upper.size.Y,
            height=p.upper.size.Z,
            align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        upper = chamfer(
            objects=upper.edges().group_by(Axis.Z)[-1],
            length=p.upper.chamfer.X,
            length2=p.upper.chamfer.Y
        )
        upper = fillet(
            objects=upper.edges().filter_by(lambda e: e.tangent_at().Z != 0),
            radius=p.upper.corner_radius
        )
        upper = fillet(
            objects=upper.edges().group_by(Axis.Z)[-1],
            radius=p.upper.fillet_radius
        )
        upper -= Cylinder(
            radius=p.stem.outer_diameter/2,
            height=BIG
        )
        upper.label = label
        upper.color = color
        return upper

@dataclass
class Lower():
    cutout_position = Vector(0, 4.93, 0)
    cutout_size = Vector(5.5, 2.95)
    corner_radius = 1
    fillet_radius = 0.5
    lip_radius = 0.5
    lip_size = Vector(15, 15, 1)
    plate_thickness = 1.65
    size = Vector(13.95, 13.95, 2.2)
    thickness = 1

@dataclass
class Pin():
    chamfer: Vector
    position: Vector | list[Vector]
    size: Vector

@dataclass
class Stem():
    # size = Vector(6.5, 6.5, 6.4)
    height = 6.4
    inner_diameter = 5.5
    outer_diameter = 6.5
    tenon_size = Vector(4, 1.3, 3.6)

@dataclass
class Upper():
    chamfer = Vector(1.5, 0.5)
    corner_radius = 1
    fillet_radius = 0.3
    size = Vector(13.95, 13.95, 3.1)
    tab_size = Vector(1, 10, 3.2)

@dataclass
class Parameters():
    lower = Lower()
    stem = Stem()
    upper = Upper()
    contact = Pin(
        chamfer=Vector(0.5, 0.3),
        position=[Vector(-5, -3.8, 0), Vector(0, -5.9, 0), Vector(5, 5.15, 0)],
        size=Vector(0.8, 0.5, 3)
    )
    center_pin = Pin(
        chamfer=Vector(0.5, 0.5),
        position=Vector(0, 0, 0),
        size=Vector(4.8, 4.8, 3.3)
    )

if __name__ == "__main__":
    from ocp_vscode import show
    show(ChocV2(travel=0))