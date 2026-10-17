from typing import Any, Dict, List, Set, Tuple
from src.core.layout.layout_interface import (
    ILayoutAnalyzer,
    TextBlock,
    RegionAnalysisResult,
)

SAME_LINE_V_OVERLAP_RATIO = 0.45
SAME_LINE_MAX_H_GAP_PX = 16.0
SAME_COL_H_OVERLAP_RATIO = 0.40
SAME_COL_MAX_V_GAP_RATIO = 0.90
LINE_CLUSTER_Y_RATIO = 0.50
Y_BUCKET_QUANTIZE_PX = 45.0
DEFAULT_MIN_DIMENSION = 1.0


class XYCutLayoutAnalyzer(ILayoutAnalyzer):
    """
    2D Spatial Layout and Reading Order Analyzer.
    Clusters word/phrase bounding boxes into coherent visual blocks (cards, diagram boxes, columns)
    and formats them hierarchically to prevent horizontal text entanglement across columns.
    """

    @staticmethod
    def _extract_box_metrics(detail: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts normalized bounding box geometry and coordinates."""
        bbox = detail["bbox"]
        xs = [float(pt[0]) for pt in bbox]
        ys = [float(pt[1]) for pt in bbox]
        x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
        h = max(DEFAULT_MIN_DIMENSION, y2 - y1)
        w = max(DEFAULT_MIN_DIMENSION, x2 - x1)
        return {
            "text": str(detail.get("text", "")).strip(),
            "confidence": float(detail.get("confidence", 0.0)),
            "x1": x1, "x2": x2, "y1": y1, "y2": y2,
            "w": w, "h": h,
            "xc": (x1 + x2) / 2.0, "yc": (y1 + y2) / 2.0,
            "raw": detail
        }

    @staticmethod
    def _are_boxes_adjacent(b1: Dict[str, Any], b2: Dict[str, Any]) -> bool:
        """Determines if two boxes belong to the same text line or multi-line block."""
        v_overlap = max(0.0, min(b1["y2"], b2["y2"]) - max(b1["y1"], b2["y1"]))
        h_overlap = max(0.0, min(b1["x2"], b2["x2"]) - max(b1["x1"], b2["x1"]))
        h_gap = max(0.0, max(b1["x1"], b2["x1"]) - min(b1["x2"], b2["x2"]))
        v_gap = max(0.0, max(b1["y1"], b2["y1"]) - min(b1["y2"], b2["y2"]))
        avg_h = (b1["h"] + b2["h"]) / 2.0

        is_same_line = v_overlap >= SAME_LINE_V_OVERLAP_RATIO * avg_h and h_gap < SAME_LINE_MAX_H_GAP_PX
        min_w = min(b1["w"], b2["w"])
        is_same_col = h_overlap >= SAME_COL_H_OVERLAP_RATIO * min_w and v_gap < SAME_COL_MAX_V_GAP_RATIO * avg_h
        return is_same_line or is_same_col

    @classmethod
    def _build_adjacency_graph(cls, boxes: List[Dict[str, Any]]) -> Dict[int, Set[int]]:
        """Constructs graph where edge exists between visually adjacent boxes."""
        n = len(boxes)
        adj: Dict[int, Set[int]] = {i: set() for i in range(n)}
        for i in range(n):
            for j in range(i + 1, n):
                if cls._are_boxes_adjacent(boxes[i], boxes[j]):
                    adj[i].add(j)
                    adj[j].add(i)
        return adj

    @classmethod
    def _traverse_component(
        cls,
        start_idx: int,
        adj: Dict[int, Set[int]],
        visited: Set[int],
        boxes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """BFS traversal to extract single connected component of boxes."""
        component = []
        queue = [start_idx]
        visited.add(start_idx)
        for cur in queue:
            component.append(boxes[cur])
            unvisited_neighbors = [nbr for nbr in adj[cur] if nbr not in visited]
            for nbr in unvisited_neighbors:
                visited.add(nbr)
                queue.append(nbr)
        return component

    @classmethod
    def _build_clusters(cls, boxes: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Clusters boxes into connected components based on 2D proximity."""
        adj = cls._build_adjacency_graph(boxes)
        visited: Set[int] = set()
        clusters: List[List[Dict[str, Any]]] = []
        for i in range(len(boxes)):
            if i not in visited:
                clusters.append(cls._traverse_component(i, adj, visited, boxes))
        return clusters

    @classmethod
    def _cluster_to_lines(cls, cluster: List[Dict[str, Any]]) -> List[str]:
        """Arranges word boxes within a cluster into horizontal lines sorted left-to-right."""
        sorted_boxes = sorted(cluster, key=lambda b: (b["y1"], b["x1"]))
        lines_dict: Dict[float, List[Dict[str, Any]]] = {}
        for b in sorted_boxes:
            matched_key = None
            for l_y in lines_dict:
                if abs(b["yc"] - l_y) < b["h"] * LINE_CLUSTER_Y_RATIO:
                    matched_key = l_y
                    break
            if matched_key is not None:
                lines_dict[matched_key].append(b)
            else:
                lines_dict[b["yc"]] = [b]

        formatted_lines = []
        for l_y in sorted(lines_dict.keys()):
            line_boxes = sorted(lines_dict[l_y], key=lambda b: b["x1"])
            formatted_lines.append(" ".join(b["text"] for b in line_boxes if b["text"]))
        return formatted_lines

    @classmethod
    def _build_text_block(cls, block_id: int, cluster: List[Dict[str, Any]]) -> TextBlock:
        """Constructs a structured TextBlock from a box cluster."""
        x1 = min(b["x1"] for b in cluster)
        x2 = max(b["x2"] for b in cluster)
        y1 = min(b["y1"] for b in cluster)
        y2 = max(b["y2"] for b in cluster)
        confs = [b["confidence"] for b in cluster if b["confidence"] > 0]
        avg_conf = (sum(confs) / len(confs)) if confs else 0.0

        lines = cls._cluster_to_lines(cluster)
        block_text = "\n".join(lines).strip()
        details = [b["raw"] for b in cluster]
        return TextBlock(
            block_id=block_id,
            bbox=(int(x1), int(y1), int(x2), int(y2)),
            lines=lines,
            text=block_text,
            confidence=avg_conf,
            word_details=details
        )

    @classmethod
    def _order_and_format_blocks(cls, blocks: List[TextBlock]) -> RegionAnalysisResult:
        """Sorts blocks in reading order and formats aggregated document text."""
        blocks.sort(key=lambda b: (round(b.bbox[1] / Y_BUCKET_QUANTIZE_PX) * Y_BUCKET_QUANTIZE_PX, b.bbox[0]))
        for i, tb in enumerate(blocks, start=1):
            tb.block_id = i

        full_sections = [f"[{tb.block_id}. Bölge]\n{tb.text}" for tb in blocks if tb.text]
        confs = [tb.confidence for tb in blocks if tb.confidence > 0]
        avg_conf = (sum(confs) / len(confs)) if confs else 0.0
        return RegionAnalysisResult(
            blocks=blocks,
            full_text="\n\n".join(full_sections),
            confidence=avg_conf
        )

    def analyze(
        self,
        word_boxes: List[Dict[str, Any]],
        image_shape: Tuple[int, int]
    ) -> RegionAnalysisResult:
        """Clusters bounding boxes into coherent 2D blocks and orders them naturally."""
        if not word_boxes:
            return RegionAnalysisResult()

        metrics_boxes = [self._extract_box_metrics(d) for d in word_boxes if str(d.get("text", "")).strip()]
        if not metrics_boxes:
            return RegionAnalysisResult()

        raw_clusters = self._build_clusters(metrics_boxes)
        blocks = [self._build_text_block(idx, c) for idx, c in enumerate(raw_clusters, start=1)]
        return self._order_and_format_blocks(blocks)

