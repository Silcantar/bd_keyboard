import os.path
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass
from enum import IntFlag, StrEnum, auto
from math import floor
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
class KeycapProfile(YAMLWizard):
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
class KeycapParameters:
    legend: str
    position: vector[2]
    profile: tuple[int, int]
    size: vector[2] = (1, 1)

@dataclass
class KeycapSet(YAMLWizard):
    profile_path: str
    keys: list[KeycapParameters]

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

def keycap_set(
    keys: list[KeycapParameters],
    profile_path: os.Pathlike = None
    ) -> list[Part]:
    if profile_path is None:
        profile_file = os.path.join(
            os.path.dirname(__file__),
            "profiles",
            "steganographer.yaml"
            )
    else:
        profile_file = os.path.join(
            os.path.dirname(__file__),
            "profiles",
            profile_path
            )
    profile = KeycapProfile.from_yaml_file(profile_file)
    profile.Stem = (
        StemChoc() if StemType.CHOC in profile.stem_type
        else StemMX()
        )
    keycaps: list[Part] = []

    for key in keys:
        column = key.profile[X]
        row = key.profile[Y]
        print_legend = (
            key.legend.replace('\n', ' ')
            if isinstance(key.legend, str)
            else key.legend
            )
        print(
            bcolors.OKBLUE
            + f"Building keycap "
            + f"R{2 - floor(key.position[Y])}C{floor(key.position[X]) + 6} — "
            + f"legend: {print_legend}."
            + bcolors.ENDC
            )
        p = deepcopy(profile)
        p.Top.angles = (
            (
                profile.Top.angles[X]
                - (row-HOME_ROW)*profile.Top.angle_increments[X]
                ),
            (
                profile.Top.angles[Y]
                - column*profile.Top.angle_increments[Y]
                )
            )
        p.Top.offsets = (
            (
                profile.Top.offsets[X]
                - column*profile.Top.offset_increments[X]
                ),
            (
                profile.Top.offsets[Y]
                + (row-HOME_ROW)*profile.Top.offset_increments[Y]
                )
            )
        height_increments = (
            abs((row-HOME_ROW)*sind(p.Top.angles[X])) * p.spacing[X] / 2,
            abs(column*sind(p.Top.angles[Y])) * p.spacing[Y] / 2
            )
        p.height = (
            profile.Stem.height
            + profile.thickness
            + sum(height_increments)
            )
        p.dimensions = key.size
        keycaps.append(
            Pos(key.position[X]*p.spacing[X], key.position[Y]*p.spacing[Y])
            * Keycap(legend=key.legend, profile=p)
            )
        keycaps[-1].label = (
            f"Keycap "
            + f"R{abs(floor(key.position[Y]))}"
            + f"C{floor(key.position[X])}"
            )
    return keycaps

class Keycap(Part):
    """Parametric keycap model."""

    def __init__(
        self,
        color: color = None,
        config: os.PathLike = None,
        label: str = None,
        legend: str = None,
        profile: KeycapProfile = None,
        **kwargs
        ):
        if config is None:
            config_file = os.path.join(
                os.path.dirname(__file__),
                "profiles",
                "steganographer.yaml"
                )
        else:
            config_file = config
        if profile is None:
            self.profile = KeycapProfile.from_yaml_file(config_file)
        else:
            self.profile = profile
        p = self.profile
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
        p = self.profile
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
        p = self.profile
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
        p = self.profile
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
        p = self.profile
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
        p = self.profile
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
        "-p",
        "--profile",
        nargs="?",
        const="steganographer.yaml"
        )
    parser.add_argument(
        "-s",
        "--set",
        nargs="?",
        const="planck.yaml"
        )
    parser.add_argument(
        "--stl",
        nargs='?',
        const=""
        )
    parser.add_argument(
        "--step",
        nargs='?',
        const=""
        )
    args = parser.parse_args()
    path = os.path.dirname(__file__)
    if args.set is not None:
        config = KeycapSet.from_yaml_file(
            os.path.join(path, "sets", args.set)
            ).__dict__
        keycaps = keycap_set(**config)
    elif args.profile is not None:
        config = KeycapProfile.from_yaml_file(
            os.path.join(path, "profiles", args.profile)
            ).__dict__
        keycaps = [Keycap(config=config)]
    else:
        keycaps = [Keycap()]
    if args.stl is not None:
        for keycap in keycaps:
            print(f"Exporting STL for {keycap.label}.")
            export_stl(
                to_export=keycap,
                file_path=os.path.join(
                    path,
                    "output",
                    "_".join([
                        args.set.replace(".yaml", ""),
                        # args.stl,
                        keycap.label.replace(" ", "_")
                        ]) + ".stl"
                    )
                )
    if args.step is not None:
        for keycap in keycaps:
            print(f"Exporting STEP for {keycap.label}.")
            export_step(
                to_export=keycap,
                file_path=os.path.join(
                    path,
                    "output",
                    "_".join([
                        args.set.replace(".yaml", ""),
                        # args.step,
                        keycap.label.replace(" ", "_")
                        ]) + ".step"
                    )
                )
    show(*keycaps)