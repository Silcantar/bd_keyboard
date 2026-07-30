import os.path
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass
from enum import IntFlag, StrEnum, auto
from os import PathLike

from build123d import *
try:
    from dataclass_wizard import YAMLWizard
except ImportError:
    from dataclass_wizard.mixins.yaml import YAMLWizard
from ocp_gordon.internal.interpolate_curve_network import CompatibilityError

try:
    from bd_keyboard.src.common import *
except ImportError:
    from common import *

HOME_ROW = 3

class LegendStyle(StrEnum):
    DOUBLESHOT = auto()
    ENGRAVED = auto()
    PRINTED = auto()

class StemType(IntFlag):
    DEFAULT = 0 # MX with no ribs.
    CHOC = auto()
    RIBBED = auto()

@dataclass
class Legend:
    color: color
    depth: float
    font: str
    font_style: str
    position: vector[2]
    print_thickness: float
    size: float
    style: LegendStyle

@dataclass
class Skirt:
    base_angle: float
    fillet_radii: vector[2]
    height: float

@dataclass
class Top:
    angles: vector[2]
    angle_increments: vector[2]
    center_points: list[vector[3]]
    center_point_references: list[float]
    center_tangents: list[float]
    offsets: vector[2]
    offset_increments: vector[2]
    ridge_angle: float
    ridge_height: float
    ridge_inset: float
    ridge_position_z: float

@dataclass
class KeycapParameters(YAMLWizard):
    clearance: float
    color: color
    dimensions: vector[2]
    label: str
    material: str
    spacing: vector[2]
    stem_type: StemType
    thickness: float
    Legend: Legend
    Skirt: Skirt
    Top: Top

@dataclass
class KeycapSetParameters(YAMLWizard):
    config: list[str]
    columns: list[int]
    rows: list[int]
    legends: list[list[str]]
    require_legend: bool

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
    columns: list[int] = [0],
    rows: list[int] = [3],
    legends: str | list[list[str]] = None,
    require_legend: bool = False
    ) -> list[Part]:
    if config is None:
        parameter_file = os.path.join(
            os.path.dirname(__file__),
            "config",
            "default.yaml"
            )
    else:
        parameter_file = os.path.join(
            os.path.dirname(__file__),
            *config
            )
    parameters = KeycapParameters.from_yaml_file(parameter_file)
    parameters.Stem = (
        StemChoc() if StemType.CHOC in parameters.stem_type
        else StemMX()
        )
    key_count = len(columns) * len(rows)
    if legends is None or isinstance(legends, str):
        legends = [[legends] * len(columns)] * len(rows)
    keycaps: list[Part] = []
    for (i, column) in enumerate(columns):
        for (j, row) in enumerate(rows):
            if (
                require_legend
                and (legends[j][i] == "" or legends[j][i] is None)
                ):
                continue
            print_legend = (
                legends[j][i].replace('\n', ' ')
                if isinstance(legends[j][i], str)
                else legends[j][i]
                )
            print(
                bcolors.OKBLUE
                + f"Building keycap R{row}C{i} — "
                + f"legend: {print_legend}."
                + bcolors.ENDC
                )
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
            p.Top.offsets = (
                (
                    parameters.Top.offsets[X]
                    - column*parameters.Top.offset_increments[X]
                    ),
                (
                    parameters.Top.offsets[Y]
                    + (row-HOME_ROW)*parameters.Top.offset_increments[Y]
                    )
                )
            height_increments = (
                abs((row-HOME_ROW)*sind(p.Top.angles[X])) * p.spacing[X] / 2,
                abs(column*sind(p.Top.angles[Y])) * p.spacing[Y] / 2
                )
            p.height = (
                parameters.Stem.height
                + parameters.thickness
                + sum(height_increments)
                )
            keycaps.append(
                Pos(
                    (i - len(columns)/2 + 0.5)*p.dimensions[X]*p.spacing[X],
                    -(j - len(rows)/2 + 0.5)*p.dimensions[Y]*p.spacing[Y]
                    )
                * Keycap(legend=legends[j][i], parameters=p)
                )
            keycaps[-1].label = f"Keycap R{row}C{i}"
    return keycaps

class Keycap(Part):
    """Parametric keycap model."""

    def __init__(
        self,
        color: color = None,
        config: os.PathLike = None,
        label: str = None,
        legend: str = None,
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
            p.height = p.Stem.height + p.thickness
        p.size = (
            p.dimensions[X]*p.spacing[X] - p.clearance,
            p.dimensions[Y]*p.spacing[Y] - p.clearance,
            p.height
            )
        self.legend = legend
        super().__init__(
            children=self._build(),
            **kwargs
            )
        self.label = p.label if label is None else label
        self.material = p.material

    def _build(self) -> list[Part]:
        p = self.parameters
        (body_outer, body_mid, body_inner) = self._body()
        stem_intersector = (
            body_mid
            + Box(10, 10, 2*p.Skirt.height, align=BOTTOM)
            )
        if StemType.CHOC in p.stem_type:
            stem = self._stem_choc() & stem_intersector
        else:
            stem = self._stem_MX() & stem_intersector
        children: list[Part] = []
        legend = self._legend()
        if legend.volume > 0:
            legend &= body_outer
            match p.Legend.style:
                case LegendStyle.DOUBLESHOT:
                    keycap = body_outer - body_mid - legend
                    legend += body_mid
                    legend -= body_inner
                    legend += stem
                case LegendStyle.ENGRAVED:
                    keycap = body_outer - body_inner - legend + stem
                case LegendStyle.PRINTED:
                    keycap = body_outer - body_inner + stem
                    legend_intersector = (
                        keycap
                        .faces()
                        .filter_by(lambda f: f.normal_at().Z > 0)
                        .sort_by(Axis.Z)[-1]
                        )
                    legend = thicken(
                        legend & legend_intersector,
                        amount=p.Legend.print_thickness
                        )
            legend.color = p.Legend.color
            legend.label = "Legend"
            children.append(legend)
        else:
            keycap = body_outer - body_inner + stem
        keycap.color = p.color
        keycap.label = "Keycap"
        children.append(keycap)
        return children

    def _body(self, solid: bool = False) -> tuple[Part, Part, Part]:
        PROFILE_COUNT = 5
        p = self.parameters
        guide_length = p.size[Y]/2 - p.spacing[Y]*p.Top.ridge_inset
        top_guides = [
            Pos(
                i * (p.size[X]/2 - p.spacing[X]*p.Top.ridge_inset),
                0,
                p.Top.ridge_position_z*p.size[Z]
                )
            * Rot(Y=90 + i*p.Top.ridge_angle)
            * SagittaArc(
                start_point=(0, -guide_length),
                end_point=(0, guide_length),
                sagitta=p.Top.ridge_height
                )
            for i in (-1, 1)
            ]
        spline_points = [
            (
                0,
                ref * (p.size[Y]/2 - point[Y]*p.spacing[Y]),
                point[Z] * p.size[Z]
                )
            for (point, ref)
            in zip(p.Top.center_points, p.Top.center_point_references)
            ]
        top_guides.insert(1, Spline(
            spline_points,
            tangents=[
                (0, cosd(angle), sind(angle))
                for angle in p.Top.center_tangents
                ]
            ))
        top_profiles = [
            ThreePointArc(
                [
                    Wire(guide).position_at(p/(PROFILE_COUNT-1))
                    for guide in top_guides
                    ]
                )
                for p in range(PROFILE_COUNT)
            ]
        try:
            face = Face.make_gordon_surface(top_profiles, top_guides)
        except CompatibilityError:
            face = Face.make_surface(top_profiles + top_guides)
        top_face = (
            Pos(*p.Top.offsets, p.height)
            * Rot(*p.Top.angles)
            * Pos(Z=-p.height)
            * face
            )
        top_face_projected = project(
            objects=top_face,
            workplane=Plane.XY
            )
        top_face_projected = fillet(
            objects=top_face_projected.vertices(),
            radius=p.Skirt.fillet_radii[1]
            )
        top_face &= extrude(
            to_extrude=top_face_projected,
            amount=BIG
            )
        base = (
            Pos(Z=p.Skirt.height)
            * RectangleRounded(*p.size[0:2], radius=p.Skirt.fillet_radii[0])
            )
        sort_reference = Vector(BIG, 2*BIG, 0)
        base_edges_sorted = base.edges().sort_by_distance(sort_reference)
        edge_pairs = [
            (
                base_edge,
                top_face.edges().sort_by_distance(base_edge.center())[0]
                )
            for base_edge in base_edges_sorted
            ]
        skirt_faces: list[Face] = []
        for edge_pair in edge_pairs:
            profiles: list[Edge] = []
            for param in range(PROFILE_COUNT):
                points = [
                    edge_pair[0].position_at(param/(PROFILE_COUNT-1)),
                    edge_pair[1].position_at(param/(PROFILE_COUNT-1))
                    ]
                base_direction = Vector(
                    points[1].X - points[0].X,
                    points[1].Y - points[0].Y,
                    ).normalized()
                tangent = (
                    base_direction.X,
                    base_direction.Y,
                    tand(p.Skirt.base_angle)
                    )
                profiles.append(
                    TangentArc(
                        points,
                        tangent=tangent
                        )
                    )
            try:
                face = Face.make_gordon_surface(profiles, edge_pair)
            except CompatibilityError:
                face = Face.make_surface(profiles + list(edge_pair))
            if face.normal_at().Z < 0:
                face = -face
            skirt_faces.append(face)
        body_shell = Shell(skirt_faces + [base, top_face])
        body_outer = Solid(body_shell)
        body_mid = scale(
            body_outer,
            by=(
                (p.size[X] - p.thickness)/p.size[X],
                (p.size[Y] - p.thickness)/p.size[Y],
                (p.size[Z] - p.thickness/2)/p.size[Z]
                ),
            about=(0, 0, p.Skirt.height)
            )
        body_inner = scale(
            body_outer,
            by=(
                (p.size[X] - 2*p.thickness)/p.size[X],
                (p.size[Y] - 2*p.thickness)/p.size[Y],
                (p.size[Z] - p.thickness)/p.size[Z]
                ),
            about=(0, 0, p.Skirt.height)
            )
        return (body_outer, body_mid, body_inner)

    def _legend(self) -> Part:
        p = self.parameters
        font_style_map = {
            "regular": FontStyle.REGULAR,
            "bold": FontStyle.BOLD,
            "italic": FontStyle.ITALIC,
            "bolditalic": FontStyle.BOLDITALIC
            }
        legend_location = (
            Pos(
                *p.Legend.position,
                p.Stem.height + (
                    p.thickness - p.Legend.depth
                    if p.Legend.style != LegendStyle.DOUBLESHOT
                    else 0
                    )
                )
            * Pos(*p.Top.offsets)
            )
        sketch = legend_location * Text(
            txt=self.legend,
            font_size=p.Legend.size,
            font=p.Legend.font,
            font_style=font_style_map[p.Legend.font_style.lower()]
            )
        legend = extrude(sketch, amount=BIG)
        return legend

    def _stem_choc(self) -> Part:
        p = self.parameters
        boss_location = Pos(Z=p.Stem.height)
        stem = (
            boss_location
            * extrude(
                RectangleRounded(
                    *p.Stem.boss_size,
                    radius=p.Stem.boss_size[Y]/2-EPS
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
        return stem

    def _stem_MX(self) -> Part:
        p = self.parameters
        stem = Cylinder(
            radius=p.Stem.radius,
            height=BIG,
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
        const="keycap"
        )
    parser.add_argument(
        "--step",
        nargs='?',
        const="keycap"
        )
    args = parser.parse_args()
    path = os.path.dirname(__file__)
    if args.config is None:
        parameters = KeycapSetParameters.from_yaml_file(
            os.path.join(path, "config", "planck_set.yaml")
            ).__dict__
        keycap_set = KeycapSet(**parameters)
    else:
        keycap = KeycapSet(config=args.config[0])
    if args.stl is not None:
        for keycap in keycap_set:
            export_stl(
                to_export=keycap,
                file_path=f"{args.stl}_{keycap.label}.stl"
                )
    if args.step is not None:
        for keycap in keycap_set:
            export_step(
                to_export=keycap,
                file_path=f"{args.step}_{keycap.label}.step"
                )
    show(keycap_set)