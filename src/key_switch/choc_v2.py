from dataclasses import dataclass

from build123d import *

try:
    from bd_keyboard.src.common import *
except ImportError:
    from common import *

class ChocV2(Part):
    """Kailh Choc V2 (CPG1353) key switch."""

    def __init__(
        self,
        travel: float = 0,
        label: str = "Choc V2 Switch",
        upper_color: ColorLike = ("White", 0.3),
        lower_color: ColorLike = ("Black", 1.0),
        stem_color: ColorLike = ("Red", 1.0),
        **kwargs
    ):
        self.parameters = Parameters()
        p = self.parameters
        children: list[Part] = []
        lower = self._lower(
            label="Lower",
            color=lower_color
            )
        children.append(lower)
        stem = Pos(Z=-travel) * self._stem(
            label="Stem",
            color=stem_color
            )
        children.append(stem)
        upper = self._upper(
            label="Upper",
            color=upper_color
            )
        children.append(upper)
        contacts = self._contacts(
            label="Contact",
            color=["Silver", "DarkGoldenrod", "Silver"]
            )
        children.extend(contacts)
        super().__init__(
            children=children,
            label=label,
            **kwargs
            )
        RigidJoint(
            label="pcb",
            to_part=self,
            joint_location=Pos(
                lower.edges()
                .filter_by(GeomType.CIRCLE)
                .filter_by(lambda e: e.radius==p.center_pin.size[X])
                .sort_by(Axis.Z)[-1]
                .arc_center
                )
            )
        RigidJoint(
            label="plate",
            to_part=self,
            joint_location=Pos(
                lower.faces()
                .filter_by(-Axis.Z)
                .sort_by(Axis.Z)[-2]
                .center()
                )
            )
        RigidJoint(
            label="keycap",
            to_part=self,
            joint_location=Pos(
                stem.faces()
                .filter_by(Axis.Z)
                .sort_by(Axis.Z)[1]
                .center()
                )
            )

    def _contacts(self, label: str, color: list[ColorLike]) -> list[Part]:
        p = self.parameters
        contact = Box(
            *p.contact.size,
            align=TOP
            )
        if Vector(p.contact.chamfer).length > 0:
            contact = chamfer(
                objects=(
                    contact.edges()
                    .group_by(Axis.Z)[0]
                    .group_by(SortBy.LENGTH)[0]
                    ),
                length=p.contact.chamfer[X],
                length2=p.contact.chamfer[Y]
                )
        contact_locs = Locations([
            Location(
                position=(
                    Vector(p.contact.position[i])
                    + Vector(0, 0, -p.lower.size[Z])
                    ),
                ) for i in range(len(p.contact.position))
            ])
        contacts = contact_locs * contact
        for i in range(len(contacts)):
            contacts[i].label = f"{label} {i+1}"
            contacts[i].color = color[i]
        return contacts

    def _lower(self, label: str, color: ColorLike) -> Part:
        p = self.parameters
        sketch = RectangleRounded(
            width=p.lower.size[X],
            height=p.lower.size[Y],
            radius=p.lower.corner_radius
            )
        lower = extrude(
            to_extrude=sketch,
            amount=-p.lower.size[Z],
            )
        lower = fillet(
            objects=lower.edges().group_by(Axis.Z)[0],
            radius=p.lower.fillet_radius
            )
        lip_sketch = RectangleRounded(
            width=p.lower.lip_size[X],
            height=p.lower.lip_size[Y],
            radius=p.lower.corner_radius
            )
        lip = extrude(
            to_extrude=lip_sketch,
            amount=p.lower.lip_size[Z]
            )
        lip_filleted = fillet(
            objects=lip.edges().group_by(Axis.Z)[-1],
            radius=p.lower.lip_radius
            )
        lower += lip_filleted
        lower -= Pos(p.lower.cutout_position) * Box(
            *p.lower.cutout_size,
            height=BIG,
            )
        lower -= (
            Pos(0, 0, -p.lower.size[Z] + p.lower.thickness)
            * Box(
                length=p.lower.size[X] - 2*p.lower.thickness,
                width=p.lower.size[Y] - 2*p.lower.thickness,
                height=BIG,
                align=BOTTOM
                )
            )
        center_pin_loc = Pos(
            lower.faces()
            .sort_by(Axis.Z)[0]
            .bounding_box()
            .center()
            + p.center_pin.position
            )
        center_pin = center_pin_loc * Cylinder(
            *p.center_pin.size,
            align=TOP
            )
        if Vector(p.center_pin.chamfer).length > 0:
            center_pin = chamfer(
                objects=center_pin.edges().sort_by(Axis.Z)[0],
                length=p.center_pin.chamfer[X],
                length2=p.center_pin.chamfer[Y]
                )
        lower += center_pin
        lower.label = label
        lower.color = color
        return lower

    def _stem(self, label: str, color: ColorLike) -> Part:
        p = self.parameters
        stem = Cylinder(
            radius=p.stem.outer_radius,
            height=p.stem.height,
            align=BOTTOM
            )
        stem -= Location(stem.faces().sort_by(Axis.Z)[-1].center())*Cylinder(
            radius=p.stem.inner_radius,
            height=p.stem.tenon_size[Z],
            align=TOP
            )
        tenon = Part(
            Locations([
                Location(
                    position=stem.faces().sort_by(Axis.Z)[-1].center(),
                    orientation=(0, 0, z)
                    )
                for z in [0, 90]
                ])
            * Box(*p.stem.tenon_size, align=TOP)
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
            *p.upper.size,
            align=BOTTOM
            )
        upper = chamfer(
            objects=upper.edges().group_by(Axis.Z)[-1],
            length=p.upper.chamfer[X],
            length2=p.upper.chamfer[Y]
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
            radius=p.stem.outer_radius,
            height=BIG
            )
        upper.label = label
        upper.color = color
        return upper

@dataclass
class Lower():
    cutout_position: vector[3] = (0, 4.93, 0)
    cutout_size: vector[2] = (5.5, 2.95)
    corner_radius: float = 1
    fillet_radius: float = 0.5
    lip_radius: float = 0.5
    lip_size: vector[3] = (15, 15, 1)
    plate_thickness: float = 1.65
    size: vector[3] = (13.95, 13.95, 2.2)
    thickness: float = 1

@dataclass
class Pin():
    chamfer: vector[2]
    position: vector[2] | Sequence[vector[2]]
    size: vector[2] | vector[3]

@dataclass
class Stem():
    # size = Vector(6.5, 6.5, 6.4)
    height: float = 6.4
    inner_radius: float = 5.5/2
    outer_radius: float = 6.5/2
    tenon_size: vector[3] = (4, 1.3, 3.6)

@dataclass
class Upper():
    chamfer: vector[2] = (1.5, 0.5)
    corner_radius: float = 1
    fillet_radius: float = 0.3
    size: vector[3] = (13.95, 13.95, 3.1)
    tab_size: vector[3] = (1, 10, 3.2)

@dataclass
class Parameters():
    lower = Lower()
    stem = Stem()
    upper = Upper()
    contact = Pin(
        chamfer=(0.5, 0.3),
        position=[(-5, -3.8, 0), (0, -5.9, 0), (5, 5.15, 0)],
        size=(0.8, 0.5, 3)
    )
    center_pin = Pin(
        chamfer=(0.5, 0.5),
        position=(0, 0, 0),
        size=(2.4, 3.3)
    )

if __name__ == "__main__":
    from ocp_vscode import show
    show(ChocV2(travel=0), render_joints=True)