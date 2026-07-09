import os.path
from dataclasses import dataclass, field
from enum import IntFlag, auto

from build123d import *
from dataclass_wizard.mixins.yaml import YAMLWizard

try:
    from bd_keyboard.src.common import *
except ImportError:
    from common import *

class StemType(IntFlag):
    DEFAULT = 0 # MX with no ribs.
    CHOC = auto()
    RIBBED = auto()

@dataclass
class Skirt:
    bottom_fillet_radius: float
    fillet_radii: vector[2]
    height: float
    thickness: float

@dataclass
class Top:
    angles: vector[2]
    dish_radius: float
    fillet_radius: float
    inside_fillet_radius: float
    offset: vector[2]
    size: vector[2]
    spline_points: list[vector[2]]
    spline_tangents: list[float]
    spline_scalars: list[float]
    thickness: float

@dataclass
class KeycapParameters(YAMLWizard):
    color: str
    height: float
    label: str
    material: str
    size: vector[2]
    stem_type: StemType
    Skirt: Skirt
    Top: Top

@dataclass
class StemMX:
    chamfer_width: float = 0.2
    depth: float = 3.6
    radius: float = 2.7
    rib_thickness: float = 1
    size: vector[2] = (4, 1.3)

@dataclass
class StemChoc:
    boss_size: vector[2] = (0, 0)
    height: float = 0
    spacing: float = 0
    size: vector[2] = (0, 0)


class Keycap(BasePartObject):
    """Parametric keycap model."""

    def __init__(
        self,
        color: color = None,
        label: str = None,
        parameters: KeycapParameters = None,
        **kwargs
        ):
        if parameters is None:
            parameter_file = os.path.join(
                os.path.dirname(__file__),
                "assets",
                "default.yaml"
                )
            self.parameters = KeycapParameters.from_yaml_file(parameter_file)
        else:
            self.parameters = parameters
        self.parameters.Stem = (
            StemChoc() if StemType.CHOC in self.parameters.stem_type
            else StemMX()
            )
        p = self.parameters
        super().__init__(
            part=self._build(),
            **kwargs
            )
        self.color = p.color if color is None else color
        self.label = p.label if label is None else label
        self.material = p.material

    def _build(self) -> Part:
        p = self.parameters
        keycap = self._top() + self._skirt()
        keycap = fillet(
            objects=keycap.edges().sort_by(Axis.Z)[-1],
            radius=p.Top.fillet_radius
            )
        keycap = fillet(
            objects=keycap.faces().sort_by(Axis.Z)[0].edges(),
            radius=p.Skirt.bottom_fillet_radius
            )
        keycap = fillet(
            objects=(
                keycap
                .faces()
                .filter_by(GeomType.REVOLUTION)
                .sort_by(Axis.Z)[0]
                .edges()
                ),
            radius=p.Top.inside_fillet_radius
            )
        if StemType.CHOC in p.stem_type:
            keycap += self._stem_choc()
        else:
            keycap += self._stem_MX()
            keycap = keycap.clean()
        return keycap

    def _top(self, inside: bool = False) -> Part:
        p = self.parameters
        spline = Spline(
            *(
                (p.Top.size[X]*point[X], p.Top.thickness*point[Y])
                for point in p.Top.spline_points
                ),
            tangents=(
                (cosd(angle), sind(angle))
                for angle in p.Top.spline_tangents
                ),
            tangent_scalars=p.Top.spline_scalars
            )
        profile = trace(spline, line_width=p.Top.thickness)
        top = (
            Pos(Z=p.height - p.Top.thickness/2)
            * Rot(*p.Top.angles, 90)
            * Pos(Z=p.Top.dish_radius)
            * revolve(
                profiles=Pos(Y=-p.Top.dish_radius) * profile,
                axis=Axis.X
                )
            )
        intersector_profile = RectangleRounded(
            *p.Top.size,
            p.Skirt.fillet_radii[-1]
            )
        if inside:
            intersector_profile = offset(
                intersector_profile,
                amount=-p.Skirt.thickness
                )
        intersector = extrude(intersector_profile, amount=p.Top.dish_radius)
        top &= intersector
        return top

    def _skirt(self, solid: bool = False) -> Part:
        p = self.parameters
        top = self._top()
        top_profile = (
            top
            .faces()
            .filter_by(GeomType.REVOLUTION)
            .sort_by(Axis.Z)[-1]
            )
        bottom_profile = Pos(Z=p.Skirt.height) * RectangleRounded(
            *p.size,
            radius=p.Skirt.fillet_radii[0]
            )
        skirt = loft([top_profile, bottom_profile])
        if not solid:
            top_inside = self._top(inside=True)
            top_inside_profile = (
                top_inside
                .faces()
                .filter_by(GeomType.REVOLUTION)
                .sort_by(Axis.Z)[-1]
                )
            bottom_inside_profile = (
                Pos(Z=p.Skirt.height)
                * RectangleRounded(
                    *(dim - 2*p.Skirt.thickness for dim in p.size),
                    radius=max(
                        p.Skirt.fillet_radii[0] - p.Skirt.thickness,
                        EPS
                        )
                    )
                )
            skirt_inside = loft([top_inside_profile, bottom_inside_profile])
            skirt -= skirt_inside
        return skirt


    def _stem_choc(self) -> Part:
        p = self.parameters
        raise NotImplementedError("Choc stem not implemented yet.")

    def _stem_MX(self) -> Part:
        p = self.parameters
        stem = Cylinder(
            radius=p.Stem.radius,
            height=p.height,
            align=BOTTOM
            )
        if StemType.RIBBED in p.stem_type:
            stem += [
                Pos(Z=p.Stem.depth)
                * Rot(Z=i*90)
                * Box(
                    length=BIG,
                    width=p.Stem.rib_thickness,
                    height=p.height - p.Stem.depth,
                    align=BOTTOM
                    )
                for i in range(2)
                ]
        stem -= [
            Rot(Z=i*90)
            * Box(
                *p.Stem.size,
                height=p.Stem.depth,
                align=BOTTOM
                )
            for i in range(2)
            ]
        stem = chamfer(
            objects=(
                stem
                .faces()
                .sort_by(Axis.Z)[0]
                .edges()
                .filter_by(GeomType.LINE)
                ),
            length=p.Stem.chamfer_width
            )
        stem &= (
            Pos(Z=-2*EPS) * self._skirt(solid=True)
            + Cylinder(
                radius=p.Stem.radius,
                height=p.Skirt.height,
                align=BOTTOM
                )
            )
        return stem


if __name__ == "__main__":
    from ocp_vscode import show
    show(Keycap())