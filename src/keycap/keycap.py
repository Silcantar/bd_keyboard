from dataclasses import dataclass

from build123d import *
from dataclass_wizard import YAMLWizard

try:
    from bd_keyboard.src.common import *
except ImportError:
    from common import *

@dataclass
class Skirt:
    bottom_fillet_radius: float = 0.5
    fillet_radii: vector[2] = (2, 6)
    height: float = 1
    thickness: float = 2

@dataclass
class Stem:
    stem_type: StemType = StemType.MX

@dataclass
class Top:
    angles: vector[2] = (5, 0)
    dish_radius: float = 30
    fillet_radius: float = 2
    inside_fillet_radius: float = 0.5
    offset: vector[2] = (0, 1)
    size: vector[2] = 15, 15
    spline_points: tuple[vector[2]] = (
        (-0.5, 0.2),
        (-0.4, 0.3),
        (0, 0),
        (0.4, 0.3),
        (0.5, 0.2)
        )
    spline_tangents: tuple[float] = (30, 0, 0, 0, -30)
    spline_scalars: tuple[float] = (1, 1, 2, 1, 1)
    thickness: float = 2

class KeycapParameters(YAMLWizard):
    color: color = "CornflowerBlue"
    height: float = 6
    label: str = "Keycap"
    material: str = "PBT"
    size: vector[2] = (18, 18)
    Skirt: Skirt = Skirt()
    Stem: Stem = Stem()
    Top: Top = Top()

class Keycap(BasePartObject):
    """Parametric keycap model."""

    def __init__(
        self,
        color: color = None,
        label: str = None,
        parameters: KeycapParameters = KeycapParameters(),
        **kwargs
        ):
        self.parameters = p = parameters
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
            bottom_inside_profile = RectangleRounded(
                *(dim - 2*p.Skirt.thickness for dim in p.size),
                radius=max(p.Skirt.fillet_radii[0] - p.Skirt.thickness, EPS)
                )
            skirt_inside = loft([top_inside_profile, bottom_inside_profile])
            skirt -= skirt_inside
        return skirt


    def _stem(self) -> Part:
        p = self.parameters


if __name__ == "__main__":
    from ocp_vscode import show
    show(Keycap())