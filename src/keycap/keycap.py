import os.path
from copy import deepcopy
from dataclasses import dataclass, field
from enum import IntFlag, auto

from build123d import *
try:
    from dataclass_wizard import YAMLWizard
except ImportError:
    from dataclass_wizard.mixins.yaml import YAMLWizard

try:
    from bd_keyboard.src.common import *
except ImportError:
    from common import *

HOME_ROW = 3

class StemType(IntFlag):
    DEFAULT = 0 # MX with no ribs.
    CHOC = auto()
    RIBBED = auto()

@dataclass
class Skirt:
    blended_corner: bool
    bottom_fillet_radius: float
    fillet_radii: vector[2]
    height: float
    sagitta: float
    thickness: float

@dataclass
class Top:
    angles: vector[2]
    angle_increments: vector[2]
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
    clearance: float
    color: str
    label: str
    material: str
    spacing: vector[2]
    stem_type: StemType
    Skirt: Skirt
    Top: Top

@dataclass
class StemMX:
    chamfer_width: float = 0.2
    height: float = 3.6
    radius: float = 2.7
    rib_thickness: float = 1
    size: vector[2] = (4, 1.3)

@dataclass
class StemChoc:
    boss_size: vector[2] = (10, 5)
    chamfer_length: float = 0.2
    height: float = 2
    rib_thickness: float = 1
    spacing: float = 5.7
    size: vector[2] = (1.2, 3)

def KeycapSet(
    config: os.Pathlike = None,
    rows: list[int] = [1, 2, 3],
    columns: list[int] = [-1, 0, 1]
    ) -> list[Part]:
    if config is None:
        parameter_file = os.path.join(
            os.path.dirname(__file__),
            "config",
            "default.yaml"
            )
    else:
        parameter_file = config
    parameters = KeycapParameters.from_yaml_file(parameter_file)
    parameters.Stem = (
        StemChoc() if StemType.CHOC in parameters.stem_type
        else StemMX()
        )
    keycaps: list[Part] = []
    for (i, column) in enumerate(columns):
        for (j, row) in enumerate(rows):
            p = deepcopy(parameters)
            p.Top.angles = (
                (
                    parameters.Top.angles[X]
                    - (row-HOME_ROW)*parameters.Top.angle_increments[X]
                    ),
                (
                    parameters.Top.angles[Y]
                    - column*parameters.Top.angle_increments[Y]
                    )
                )
            height_increments = (
                abs((row-HOME_ROW)*sind(p.Top.angles[X])) * p.spacing[X] / 2,
                abs(column*sind(p.Top.angles[Y])) * p.spacing[Y] / 2
                )
            p.height = (
                parameters.Stem.height
                + parameters.Top.thickness
                + sum(height_increments)
                )
            keycaps.append(
                Pos(
                    (i - len(columns)/2 + 0.5)*p.spacing[X],
                    -(j - len(rows)/2 + 0.5)*p.spacing[Y]
                    )
                * Keycap(parameters=p)
                )
            keycaps[-1].label = f"Keycap R{row}C{i}"
    return keycaps

class Keycap(BasePartObject):
    """Parametric keycap model."""

    def __init__(
        self,
        color: color = None,
        label: str = None,
        config: os.PathLike = None,
        parameters: KeycapParameters = None,
        **kwargs
        ):
        if config is None:
            parameter_file = os.path.join(
                os.path.dirname(__file__),
                "config",
                "default.yaml"
                )
        else:
            parameter_file = config
        if parameters is None:
            self.parameters = KeycapParameters.from_yaml_file(parameter_file)
        else:
            self.parameters = parameters
        p = self.parameters
        try:
            p.Stem
        except AttributeError:
            p.Stem = (
                StemChoc() if StemType.CHOC in p.stem_type
                else StemMX()
                )
        try:
            p.height
        except AttributeError:
            p.height = p.Stem.height + p.Top.thickness
        super().__init__(
            part=self._build(),
            **kwargs
            )
        self.color = p.color if color is None else color
        self.label = p.label if label is None else label
        self.material = p.material

    def _build(self) -> Part:
        p = self.parameters
        top = self._top()
        if StemType.CHOC in p.stem_type:
            stem = self._stem_choc()
        else:
            stem = self._stem_MX()
        skirt = split(
            objects=self._skirt() + stem,
            bisect_by=top.faces().sort_by(SortBy.AREA)[-1],
            keep=Keep.BOTTOM
            )
        top_intersector = self._skirt(solid=True)
        keycap = skirt + (top & top_intersector)
        if p.Skirt.bottom_fillet_radius > 0:
            keycap = fillet(
                objects=keycap.faces().filter_by(
                    lambda f: f.center().Z == p.Skirt.height
                    ).edges(),
                radius=p.Skirt.bottom_fillet_radius
                )
        if p.Top.fillet_radius > 0:
            keycap = fillet(
                objects=keycap.edges().sort_by(Axis.Z)[-1],
                radius=p.Top.fillet_radius
                )
        if p.Top.inside_fillet_radius > 0:
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
        return keycap.clean()

    def _skirt(self, solid: bool = False) -> Part:
        p = self.parameters
        Shape = RectangleBlended if p.Skirt.blended_corner else RectangleRounded
        size = tuple(dim - p.clearance for dim in p.spacing)
        height = (
            p.height
            + p.Top.size[X]/2 * tan(asin(p.Top.size[X]/2/p.Top.dish_radius)/2)
            + 1
            )
        profiles: list[Face] = []
        profiles.append(
            Pos(*p.Top.offset, height)
            * Rot(*p.Top.angles, 0)
            * Shape(
                *p.Top.size,
                radius=p.Skirt.fillet_radii[1]
                )
            )
        # Middle profiles
        if p.Skirt.sagitta > 0:
            profiles.append(
                Pos(Z=(p.height-p.Skirt.height)/2 + p.Skirt.height)
                * Shape(
                    *(
                        (skirt_size+top_size)/2 + p.Skirt.sagitta
                        for (skirt_size, top_size) in zip(size, p.Top.size)
                        ),
                        radius=sum(p.Skirt.fillet_radii)/2
                    )
                )
        profiles.append(
            Pos(Z=p.Skirt.height)
            * Shape(
                *size,
                radius=p.Skirt.fillet_radii[0]
                )
            )
        skirt = loft(profiles)
        if not solid:
            skirt -= scale(
                objects=skirt,
                by=(*((dim - 2*p.Skirt.thickness)/dim for dim in size), 1),
                )
        return skirt

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
        spline = scale(spline, by=(1, 1/cosd(p.Top.angles[X]), 1))
        profile = trace(spline, line_width=p.Top.thickness)
        top = (
            Pos(*p.Top.offset, p.height)
            * Rot(*p.Top.angles, 90)
            * Pos(Z=p.Top.dish_radius)
            * revolve(
                profiles=Pos(Y=-p.Top.dish_radius) * profile,
                axis=Axis.X
                )
            )
        return top

    def _stem_choc(self) -> Part:
        p = self.parameters
        boss_location = Pos(Z=p.Stem.height)
        stem = (
            boss_location
            * extrude(
                RectangleRounded(
                    *p.Stem.boss_size,
                    radius=p.Stem.boss_size[Y]/2
                    ),
                amount=BIG
                )
            )
        tenon_locations = [
            Pos(X=i*p.Stem.spacing/2)
            for i in (-1, 1)
            ]
        stem += (
            tenon_locations
            * Box(*p.Stem.size, p.Stem.height, align=BOTTOM)
            )
        stem = chamfer(
            stem.edges().group_by(Axis.Z)[0],
            length=p.Stem.chamfer_length
            )
        if StemType.RIBBED in p.stem_type:
            stem += [
                Pos(Z=p.Stem.size[Z])
                * Rot(Z=i*90)
                * Box(
                    length=BIG,
                    width=p.Stem.rib_thickness,
                    height=BIG,
                    align=BOTTOM
                    )
                for i in range(2)
                ]
        stem &= (
            Pos(Z=-2*EPS) * self._skirt(solid=True)
            + Cylinder(
                radius=max(p.Stem.boss_size),
                height=p.Skirt.height,
                align=BOTTOM
                )
            )
        return stem

    def _stem_MX(self) -> Part:
        p = self.parameters
        stem = Cylinder(
            radius=p.Stem.radius,
            height=p.Stem.height + p.Top.thickness,
            align=BOTTOM
            )
        if StemType.RIBBED in p.stem_type:
            stem += [
                Pos(Z=p.Stem.height)
                * Rot(Z=i*90)
                * Box(
                    length=BIG,
                    width=p.Stem.rib_thickness,
                    height=BIG,
                    align=BOTTOM
                    )
                for i in range(2)
                ]
        stem -= [
            Rot(Z=i*90)
            * Box(
                *p.Stem.size,
                height=p.Stem.height,
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
    import argparse
    from ocp_vscode import show
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "-p",
        "--config",
        "--parameters",
        nargs=1,
        )
    parser.add_argument(
        "-s",
        "--set",
        nargs='?'
        )
    parser.add_argument(
        "--stl",
        nargs='?',
        const="keycap.stl"
        )
    parser.add_argument(
        "--step",
        nargs='?',
        const="keycap.step"
        )
    args = parser.parse_args()
    if args.config is None:
        keycap = Keycap()
    else:
        keycap = Keycap(config=args.config[0])
    if args.stl is not None:
        export_stl(
            to_export=keycap,
            file_path=args.stl
            )
    if args.step is not None:
        export_step(
        to_export=keycap,
        file_path=args.step
        )
    keycap_set = KeycapSet()
    show(keycap_set)