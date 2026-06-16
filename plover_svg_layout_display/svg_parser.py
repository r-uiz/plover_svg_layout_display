from typing import List, Dict
import lxml.etree as ET

from plover_svg_layout_display.qt_utils import load_qt_text
from plover_svg_layout_display.resources_rc import *


SVG_TEMPLATE = (
    "<svg{header}>\n{content}\n</svg>"
)


class SVGParser:
    
    __slots__ = ["group_svgs", "svg_attribs", "svg_raw"]

    def load_file(self, path: str) -> List[str]:
        parser = ET.XMLParser(recover=True)
        self.svg_raw = load_qt_text(path)
        tree = ET.fromstring(self.svg_raw.encode("utf-8"), parser)

        self.group_svgs: Dict[str, str] = {}
        for child in tree:
            tag = child.tag
            if "}" in tag:
                tag = tag.split("}", 1)[1]

            if tag == "g" and "id" in child.attrib:
                self.group_svgs[child.attrib["id"]] = ET.tostring(child).decode()

        if "<svg" in self.svg_raw:
            self.svg_attribs = self.svg_raw.split("<svg", 1)[1].split(">")[0]


    def get_svg_content(
        self, 
        group_ids: List[str]
    ) -> str:
        content = "\n".join(
            self.group_svgs[id] 
            for id in group_ids
            if id in self.group_svgs
        )

        return SVG_TEMPLATE.format(
            header=self.svg_attribs,
            content=content
        )
    
    def get_whole_svg(self) -> str:
        return self.get_svg_content(self.group_svgs.keys())

    def get_blend_svg(
        self,
        base_ids: List[str],
        fade_ids: List[str],
        top_ids: List[str],
        alpha: float
    ) -> str:
        # Cross-fade for the auto-clear: neutral caps underneath, the pressed
        # caps drawn on top at `alpha` (1 -> 0 reveals neutral in place), then
        # any always-on groups (finger guides) above everything.
        def join(ids):
            return "\n".join(
                self.group_svgs[id] for id in ids if id in self.group_svgs
            )

        content = join(base_ids)
        fade = join(fade_ids)
        if fade:
            content += "\n<g opacity=\"%.3f\">\n%s\n</g>" % (alpha, fade)
        top = join(top_ids)
        if top:
            content += "\n" + top

        return SVG_TEMPLATE.format(
            header=self.svg_attribs,
            content=content
        )
