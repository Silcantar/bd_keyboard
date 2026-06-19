from dataclasses import dataclass

from build123d import *

try:
    from bd_keyboard.src.common import *
except ImportError:
    from common import *

@dataclass
class NiceViewParameters:
    color: ColorLike = (0x202020, 1)
    bezel: float = 1.6
    chip_size: vector[3] = (10, 10, 1)
    display_area: vector[2] = (10.8, 25.3)
    fillet_radius: float = 1
    hole_count: int = 5
    hole_id: float = 1
    hole_od: float = 2
    hole_spacing: float = 2.54
    pcb_size: vector[3] = (14, 36, 1)
    position: float = 3
    size: vector[3] = (13.8, 29.35, 0.9)

class NiceView(BasePartObject):
    """OLED/LCD/ePaper display like Nice!View or similar."""
    def __init__(
        self,
        parameters: NiceViewParameters = NiceViewParameters(),
        label: str = "Nice!View",
        **kwargs
    ):
        self.parameters = parameters
        super().__init__(part=self._build(), **kwargs)
        self.label = label

    def _build(self) -> Part:
        p = self.parameters
        children: list[Part] = []
        pcb_location = Pos(Z=-p.size[Z])
        pcb = (
            pcb_location
            * Box(
                *p.pcb_size,
                align=BACK_TOP
                )
            )
        pcb = fillet(
            objects=pcb.edges().filter_by(Axis.Z),
            radius=p.fillet_radius
            )
        hole_locations = [
            Pos(
                i*p.hole_spacing,
                -p.hole_spacing/2,
                -p.size[Z]
                )
            for i in range(-(p.hole_count//2), p.hole_count//2+1)
            ]
        pcb -= (
            hole_locations
            * Cylinder(
                radius=p.hole_od/2,
                height=BIG
                )
            )
        hole = (
            Cylinder(
                radius=p.hole_od/2,
                height=p.pcb_size[Z],
                align=TOP
                )
            - Cylinder(
                radius=p.hole_id/2,
                height=BIG
                )
            )
        holes = Part(hole_locations * hole)
        holes.label = "Holes"
        holes.color = "Goldenrod"
        children.append(holes)
        pcb.label = "PCB"
        pcb.color = p.color
        children.append(pcb)
        bezel_location = Pos(Y=-p.position)
        bezel = (
            bezel_location
            * Box(
                *p.size,
                align=BACK_TOP
                )
            )
        display_location = Pos(Y=-p.position - p.bezel)
        display = (
            display_location
            * Box(
                *p.display_area,
                p.size[Z],
                align=BACK_TOP
                )
            )
        bezel -= display
        bezel.label = "Bezel"
        bezel.color = p.color
        children.append(bezel)
        display.label = "Display Area"
        display.color = "Gray"
        children.append(display)
        chip_location = Pos(
            0,
            -p.pcb_size[Y]/2,
            -p.size[Z] - p.pcb_size[Z]
            )
        chip = (
            chip_location
            * Box(
                *p.chip_size,
                align=TOP
                )
            )
        chip.label = "Chips Placeholder"
        chip.color = p.color
        children.append(chip)
        return Compound(children=children)


if __name__ == "__main__":
    from ocp_vscode import show
    show(NiceView())