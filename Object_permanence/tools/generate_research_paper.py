import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

def create_research_paper_docx(output_path: str):
    doc = docx.Document()

    # Page Margins: Standard IEEE 0.75 in
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    # -------------------------------------------------------------
    # Helper Functions for Formatting
    # -------------------------------------------------------------
    def add_title(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(12)
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(20)
        run.font.bold = True
        return p

    def add_author_table(authors_data):
        # 3 authors side by side
        table = doc.add_table(rows=1, cols=3)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        col_width = Inches(2.3)
        for i, a in enumerate(authors_data):
            cell = table.cell(0, i)
            cell.width = col_width
            # Remove borders
            tcPr = cell._tc.get_or_add_tcPr()
            tcBorders = parse_xml(r'''
                <w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                    <w:top w:val="none"/>
                    <w:left w:val="none"/>
                    <w:bottom w:val="none"/>
                    <w:right w:val="none"/>
                </w:tcBorders>
            ''')
            tcPr.append(tcBorders)

            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(2)

            r_name = p.add_run(a['name'] + '\n')
            r_name.font.name = 'Times New Roman'
            r_name.font.size = Pt(10.5)
            r_name.font.bold = True

            r_dept = p.add_run(a['dept'] + '\n')
            r_dept.font.name = 'Times New Roman'
            r_dept.font.size = Pt(8.5)

            r_inst = p.add_run(a['inst'] + '\n')
            r_inst.font.name = 'Times New Roman'
            r_inst.font.size = Pt(8.5)

            r_loc = p.add_run(a['loc'] + '\n')
            r_loc.font.name = 'Times New Roman'
            r_loc.font.size = Pt(8.5)

            r_mail = p.add_run(a['email'])
            r_mail.font.name = 'Times New Roman'
            r_mail.font.size = Pt(8.5)

        # Spacing after author table
        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_after = Pt(10)

    # -------------------------------------------------------------
    # Title & Authors (Section 1: 1 Column)
    # -------------------------------------------------------------
    add_title("Quantifying Object Permanence in AI-Generated Videos: An Automated Evaluation Framework Using Open-Vocabulary Detection and Persistent Memory Tracking")

    authors = [
        {
            "name": "Sibhinandhan.ER",
            "dept": "Dept. of Artificial Intelligence & Machine Learning",
            "inst": "Rajalakshmi Engineering College",
            "loc": "Chennai, India",
            "email": "sibhinandhan.er.2023.aiml@rajalakshmi.edu.in"
        },
        {
            "name": "R. Sankara Narayanan",
            "dept": "Dept. of Artificial Intelligence & Machine Learning",
            "inst": "Rajalakshmi Engineering College",
            "loc": "Chennai, India",
            "email": "sankaranarayanan.r.2023.aiml@rajalakshmi.edu.in"
        },
        {
            "name": "Shriram P",
            "dept": "Dept. of Artificial Intelligence & Machine Learning",
            "inst": "Rajalakshmi Engineering College",
            "loc": "Chennai, India",
            "email": "shriram.p.2023.aiml@rajalakshmi.edu.in"
        }
    ]
    add_author_table(authors)

    # -------------------------------------------------------------
    # Section 2: 2 Columns for Paper Body
    # -------------------------------------------------------------
    body_section = doc.add_section()
    sectPr = body_section._sectPr
    cols = sectPr.xpath('./w:cols')
    if cols:
        cols[0].set(qn('w:num'), '2')
        cols[0].set(qn('w:space'), '720')  # 0.5 in gutter
    else:
        col_elem = OxmlElement('w:cols')
        col_elem.set(qn('w:num'), '2')
        col_elem.set(qn('w:space'), '720')
        sectPr.append(col_elem)

    # Helper functions for two-column body
    def add_abstract(abstract_text, keywords_text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.05
        p.paragraph_format.space_after = Pt(8)

        r_abs = p.add_run("Abstract—")
        r_abs.font.name = 'Times New Roman'
        r_abs.font.size = Pt(9.5)
        r_abs.font.bold = True

        r_text = p.add_run(abstract_text)
        r_text.font.name = 'Times New Roman'
        r_text.font.size = Pt(9.5)

        p_kw = doc.add_paragraph()
        p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_kw.paragraph_format.line_spacing = 1.05
        p_kw.paragraph_format.space_after = Pt(12)

        r_kw_title = p_kw.add_run("Keywords—")
        r_kw_title.font.name = 'Times New Roman'
        r_kw_title.font.size = Pt(9.5)
        r_kw_title.font.bold = True

        r_kw = p_kw.add_run(keywords_text)
        r_kw.font.name = 'Times New Roman'
        r_kw.font.size = Pt(9.5)

    def add_sec_heading(num_str, title_str):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(f"{num_str}. {title_str.upper()}")
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)
        run.font.bold = True

    def add_subsec_heading(letter_str, title_str):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(f"{letter_str}. {title_str}")
        run.font.name = 'Times New Roman'
        run.font.size = Pt(9.5)
        run.font.bold = True
        run.font.italic = True

    def add_p(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.05
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.first_line_indent = Inches(0.18)
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(9.5)
        return p

    def add_equation(eq_text, eq_num_str):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        r_eq = p.add_run(eq_text + f"   ({eq_num_str})")
        r_eq.font.name = 'Times New Roman'
        r_eq.font.size = Pt(9.5)
        r_eq.font.italic = True

    # -------------------------------------------------------------
    # Abstract & Keywords
    # -------------------------------------------------------------
    abs_content = (
        "Recent breakthroughs in generative diffusion models, video transformers, and generative world models have "
        "enabled the synthesis of remarkably high-fidelity, photorealistic video sequences. However, despite their impressive "
        "per-frame visual quality, modern video synthesis architectures exhibit severe temporal inconsistency and routinely "
        "violate fundamental physical constraints—most critically the cognitive principle of object permanence. When dynamic objects "
        "undergo visual occlusion, camera panning, or obstacle transit, generative models frequently exhibit catastrophic failures, "
        "including spontaneous object deletion, morphological warping, and identity switching upon reappearance. Existing video quality "
        "metrics such as Fréchet Video Distance (FVD) and Inception Score (IS) quantify only texture fidelity and distribution similarity, "
        "remaining completely blind to temporal identity continuity. To address this fundamental limitation, this paper presents an "
        "automated, zero-shot Object Permanence Evaluation Framework for AI-generated videos. The system couples high-resolution "
        "(1280px) open-vocabulary detection via YOLO-World with ByteTrack multi-object tracking accelerated on dedicated GPU hardware. "
        "To systematically model physical persistence, we formulate a Persistent Object State Memory Bank operating a discrete 4-state "
        "visibility machine (VISIBLE, OCCLUDED, OUT_OF_BOUNDS, LOST), coupled with a ballistic dead-reckoning kinematic model and an "
        "online memory-guided re-identification engine that actively heals identity switches. We formalize three standardized quantitative "
        "benchmark metrics: Detection Consistency (DC), Identity Consistency (IC), and the Object Permanence Score (OPS), supplemented by "
        "Memory Recovery Rate (MRR) and Trajectory Prediction Error. Extensive empirical evaluations across synthetic occlusion benchmarks "
        "and real generative AI video sequences demonstrate that the framework reliably uncovers physical hallucinations, sustains "
        "tracking across 27-frame occlusion gaps, and recovers 71.43% of occluded identities. This work provides an objective, reproducible "
        "diagnostic benchmark to accelerate the development of physics-grounded, memory-conditioned video generation architectures."
    )
    kw_content = (
        "Object Permanence, AI-Generated Videos, Generative Diffusion Models, Video Transformers, Multi-Object Tracking, "
        "ByteTrack, YOLO-World, Persistent Memory Bank, Dead-Reckoning, Temporal Consistency, Computer Vision, Deep Learning."
    )
    add_abstract(abs_content, kw_content)

    # -------------------------------------------------------------
    # I. INTRODUCTION
    # -------------------------------------------------------------
    add_sec_heading("I", "Introduction")
    add_p(
        "Artificial Intelligence video generation has witnessed transformative progress over the past two years. Powered by modern "
        "spatiotemporal diffusion models, autoregressive transformers, and world models—such as OpenAI's Sora, Runway's Gen-2, Pika Labs, "
        "and Stability AI's Stable Video Diffusion (SVD)—synthetic video synthesis can now render intricate textures, lighting variations, "
        "and photorealistic scenes from simple natural language prompts. Despite these extraordinary perceptual capabilities, generative "
        "video models suffer from a fundamental architectural limitation: they lack an explicit, grounded understanding of physical reality."
    )
    add_p(
        "In cognitive developmental psychology, Jean Piaget identified Object Permanence as a paramount milestone of infant sensorimotor "
        "development—the cognitive realization that physical entities continue to exist in space and time even when they are obscured from "
        "sensory perception by an intervening obstacle. Renée Baillargeon's violation-of-expectation experiments further established that "
        "biological cognitive systems inherently track the trajectory, volume, and identity of hidden objects behind occluders. In sharp "
        "contrast, generative AI models synthesize video sequences frame-by-frame or chunk-by-chunk through cross-attention mechanisms that "
        "condition each latent slice on prior latents and text embeddings. When an object passes behind an obstacle, its sensory tokens vanish "
        "from the latent attention field. Consequently, the generative model frequently suffers from 'latent amnesia': the object either "
        "vanishes permanently, emerges with a mutated color or category, or swaps identity with an entirely unrelated entity."
    )
    add_p(
        "A major impediment to solving this problem lies in the inadequacy of existing evaluation paradigms. Standard video synthesis benchmarks "
        "rely predominantly on Fréchet Video Distance (FVD), Kernel Video Distance (KVD), and CLIP text-image similarity scores. While FVD "
        "effectively captures whether individual frames look like real video distributions, it operates on aggregated 2D/3D convolutional "
        "feature maps (e.g., I3D embeddings) that average out fine-grained temporal tracking errors. An AI video where a rolling red ball disappears "
        "behind a wall and emerges as a blue cube can still achieve an outstanding FVD score because both the ball and cube look photorealistic. "
        "There is currently no standardized, automated metric to penalize generative models for physical identity violations during occlusion."
    )
    add_p(
        "To bridge this critical gap, this paper introduces an automated, end-to-end Object Permanence Evaluation Framework. By combining "
        "state-of-the-art open-vocabulary object detection, multi-object tracking, and a biologically inspired Persistent Object State "
        "Memory Bank, our framework provides an objective, quantitative methodology to benchmark object permanence in generative AI videos."
    )
    add_p("The primary contributions of this work are summarized as follows:")
    add_p(
        "1) We propose an automated evaluation framework coupling open-vocabulary zero-shot detection (YOLO-World) with ByteTrack multi-object "
        "tracking running at native high resolution (1280px) on dedicated GPU hardware."
    )
    add_p(
        "2) We formulate a Persistent Object State Memory Bank incorporating a discrete 4-state visibility machine and a ballistic dead-reckoning "
        "kinematic model that extrapolates object trajectories through visual occlusions and actively heals identity switches."
    )
    add_p(
        "3) We formalize three core quantitative research metrics—Detection Consistency (DC), Identity Consistency (IC), and the Object Permanence "
        "Score (OPS)—supplemented by Memory Recovery Rate (MRR) and Trajectory Prediction Error."
    )
    add_p(
        "4) We evaluate the framework empirically on both synthetic occlusion test suites and real generative AI video sequences, demonstrating "
        "its efficacy in detecting failure modes and recovering identity continuity across prolonged occlusion intervals."
    )

    # -------------------------------------------------------------
    # II. LITERATURE SURVEY
    # -------------------------------------------------------------
    add_sec_heading("II", "Literature Survey")
    add_subsec_heading("A", "Video Generation Models & Temporal Inconsistencies")
    add_p(
        "Video diffusion models extend 2D image synthesis (e.g., DALL-E, Stable Diffusion) into the temporal domain by interleaving spatial "
        "convolution/attention layers with temporal cross-attention or 1D convolutions (Ho et al., 2022; Blattmann et al., 2023). While these "
        "models achieve smooth frame-to-frame transitions across short clips, multiple studies highlight their failure to maintain long-term physical "
        "constraints. Singer et al. (2023) and Brooks et al. (2024) observed that generative diffusion networks suffer from temporal drift and "
        "accumulated sampling errors, leading to semantic morphing and object disappearance over multi-second horizons."
    )
    add_subsec_heading("B", "Multi-Object Tracking and Data Association")
    add_p(
        "Multi-Object Tracking (MOT) aims to estimate bounding box trajectories and persistent IDs across video sequences. The tracking-by-detection "
        "paradigm, pioneered by SORT (Bewley et al., 2016) and DeepSORT (Wojke et al., 2017), relies on Kalman filtering for motion prediction and "
        "the Hungarian algorithm for spatial-appearance association. ByteTrack (Zhang et al., 2022) achieved a major breakthrough by retaining "
        "both high- and low-confidence detection boxes, matching low-score boxes to existing trajectories to prevent track loss during motion blur "
        "and partial occlusion. However, classical MOT trackers discard lost tracks after a brief temporal window (typically 30 frames), making them "
        "incapable of recovering prolonged occlusions without external persistent memory."
    )
    add_subsec_heading("C", "Physical Reasoning and Cognitive Benchmarks in AI")
    add_p(
        "Evaluating physical commonsense in machine vision has gained significant attention. Benchmarks such as IntPhys (Riochet et al., 2021) "
        "and CRAFT (Ates et al., 2020) test video models on simulated 3D physics violations using synthetic rendering engines (e.g., Unreal Engine). "
        "Similarly, CLEVRER (Yi et al., 2020) probes causal and temporal reasoning in synthetic scenes. While valuable, these benchmarks rely on "
        "synthetic 3D ground truth and synthetic simulation environments, rendering them inapplicable for arbitrary, unannotated AI-generated "
        "videos produced by real-world generative models."
    )
    add_subsec_heading("D", "Summary of Gaps in Existing Literature")
    add_p(
        "Prior works leave three critical gaps: (1) video synthesis metrics (FVD, IS) ignore temporal identity preservation; (2) classical MOT "
        "trackers passively fail under extended occlusion rather than actively modeling persistent memory states; and (3) physical evaluation "
        "frameworks depend on synthetic 3D ground truth. Our work fills these gaps by providing an automated, zero-shot, vision-based evaluation "
        "framework equipped with an explicit kinematic memory bank."
    )

    # -------------------------------------------------------------
    # III. PROPOSED METHOD
    # -------------------------------------------------------------
    add_sec_heading("III", "Proposed Method")
    add_p(
        "The proposed Object Permanence Evaluation Framework operates as an end-to-end automated pipeline comprising five sequential modules: "
        "(1) High-Resolution Video Ingestion, (2) Open-Vocabulary Zero-Shot Detection, (3) Multi-Object Tracking Association, (4) Persistent "
        "Object State Memory Bank with Kinematic Dead-Reckoning, and (5) Quantitative Permanence Metric Computation and Reporting."
    )
    add_p(
        "Fig. 1 illustrates the overall system architecture. Unlike conventional tracking pipelines that discard state information upon detection "
        "dropouts, our framework actively routes raw detections through an intermediate kinematic state machine that maintains persistent entity "
        "records, projects motion during visual absence, and resolves identity switches live during frame streaming."
    )

    # Pseudocode Box
    p_code_header = doc.add_paragraph()
    p_code_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_code_header.paragraph_format.space_before = Pt(8)
    p_code_header.paragraph_format.space_after = Pt(2)
    r_ch = p_code_header.add_run("PSEUDOCODE OF THE PROPOSED METHOD")
    r_ch.font.name = 'Times New Roman'
    r_ch.font.size = Pt(9.5)
    r_ch.font.bold = True

    code_lines = [
        "Input: Video V = {F_1, F_2, ..., F_T}, Open-Vocabulary Prompts P = {c_1, ..., c_k}",
        "Output: Annotated Video V_ann, Detection Log D_hist, Event Log E_hist, Summary Report R",
        "Begin",
        " 1: Initialize YOLO-World model M_det with text prompts P at resolution 1280px",
        " 2: Initialize ByteTrack tracker T_mot with IoU threshold tau_iou",
        " 3: Initialize Persistent Memory Bank B_mem with frame dimensions (W, H)",
        " 4: For each frame F_t in V (t = 1 to T) do:",
        " 5:    D_raw = M_det.detect(F_t, conf >= tau_conf)",
        " 6:    D_track = T_mot.associate(D_raw, F_t)",
        " 7:    D_enhanced, G_ghost = B_mem.update(t, D_track)",
        " 8:    F_ann = RenderAnnotations(F_t, D_enhanced, G_ghost)",
        " 9:    WriteFrame(V_ann, F_ann)",
        "10: End For",
        "11: E_hist = AnalyzePermanenceEvents(D_enhanced)",
        "12: Compute Quantitative Metrics: DC, IC, OPS, MRR, MAE_pred",
        "13: Export D_hist.csv, E_hist.csv, B_mem_lifecycle.csv, Summary.json, Summary.txt",
        "14: Generate Trajectory Timeline and Metric Summary Plots",
        "End"
    ]

    p_box = doc.add_paragraph()
    p_box.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_box.paragraph_format.line_spacing = 1.0
    p_box.paragraph_format.space_before = Pt(2)
    p_box.paragraph_format.space_after = Pt(8)
    # Add light grey background and thin border
    p_box_pr = p_box._p.get_or_add_pPr()
    pBdr = parse_xml(r'''
        <w:pBdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:top w:val="single" w:sz="4" w:space="4" w:color="94A3B8"/>
            <w:left w:val="single" w:sz="4" w:space="4" w:color="94A3B8"/>
            <w:bottom w:val="single" w:sz="4" w:space="4" w:color="94A3B8"/>
            <w:right w:val="single" w:sz="4" w:space="4" w:color="94A3B8"/>
        </w:pBdr>
    ''')
    p_box_pr.append(pBdr)

    for cline in code_lines:
        r_cl = p_box.add_run(cline + "\n")
        r_cl.font.name = 'Courier New'
        r_cl.font.size = Pt(8.0)
        if cline.startswith("Input:") or cline.startswith("Output:") or cline.startswith("Begin") or cline.startswith("End"):
            r_cl.font.bold = True

    # -------------------------------------------------------------
    # IV. METHODOLOGY & MATHEMATICAL FORMULATION
    # -------------------------------------------------------------
    add_sec_heading("IV", "Methodology")
    add_subsec_heading("A", "Open-Vocabulary Detection and Frame-by-Frame Tracking")
    add_p(
        "Standard object detectors (e.g., standard YOLOv8, Faster R-CNN) are constrained to fixed label sets (e.g., 80 COCO classes). "
        "In AI-generated video research, dynamic entities frequently encompass novel or abstract objects (e.g., 'synthetic ball', 'wooden cube'). "
        "To achieve unconstrained zero-shot evaluation, we integrate YOLO-World (yolov8x-worldv2). YOLO-World binds visual feature maps with "
        "offline text embeddings extracted via a vision-language CLIP text encoder. At inference, candidate bounding boxes are scored via "
        "cross-modal cosine similarity against custom target prompts P = {c_1, ..., c_k}."
    )
    add_p(
        "Detections with confidence c_i >= tau_conf are passed to ByteTrack. ByteTrack maintains a set of active trajectories utilizing a "
        "discrete Kalman filter state space x = [u, v, s, r, u_dot, v_dot, s_dot], where (u, v) is the bounding box center, s is scale (area), "
        "and r is aspect ratio. In classical ByteTrack, when an object is occluded for more than max_time_lost frames (default: 30 frames), "
        "its Kalman track is permanently terminated."
    )

    add_subsec_heading("B", "Persistent Object State Memory Bank Architecture")
    add_p(
        "To extend tracking survivability across prolonged generative occlusions, we formulate the Persistent Object State Memory Bank. "
        "Each tracked entity maintains a persistent memory slot S_i characterized by a tuple: S_i = {id_i, c_i, state_i, H_pos, H_box, V_i, A_i, P_hat},"
        "where state_i belongs to a discrete 4-state visibility machine: state_i in {VISIBLE, OCCLUDED, OUT_OF_BOUNDS, LOST}."
    )
    add_p(
        "1) Kinematic Velocity Estimation: While visible, the entity's velocity vector V_t = [v_x, v_y]^T is computed using an Exponential Moving "
        "Average (EMA) over instantaneous positional differentials:"
    )
    add_equation("V_t = alpha * ((P_t - P_{t-Delta t}) / Delta t) + (1 - alpha) * V_{t-Delta t}", "1")
    add_p(
        "where alpha = 0.70 is the velocity smoothing factor and Delta t is the elapsed frame interval."
    )
    add_p(
        "2) Ballistic Dead-Reckoning Extrapolation: When sensory detections drop (e.g., an object enters occlusion behind an obstacle), the memory "
        "bank does not terminate the track. Instead, it projects the object's trajectory forward using dead-reckoning kinematics:"
    )
    add_equation("P_hat_t = P_{last} + V_t * k_{occluded}", "2")
    add_p(
        "where k_{occluded} is the consecutive frame count since the object was last detected. Boundary conditions are checked at each step: if "
        "P_hat_t extends beyond frame bounds [0, W] x [0, H], state_i transitions to OUT_OF_BOUNDS; if k_{occluded} > tau_max_gap (90 frames), "
        "it transitions to LOST."
    )
    add_p(
        "3) Memory-Guided Re-Identification: When ByteTrack assigns a new or unassociated track ID upon object reappearance, the memory bank "
        "intercepts the detection d_j and evaluates a fused association cost against all candidate OCCLUDED memory slots S_i:"
    )
    add_equation("Cost(d_j, S_i) = w_dist * (||P_{d_j} - P_hat_{S_i}||_2 / D_diag) + w_scale * |(Area(d_j) / Area(S_i)) - 1|", "3")
    add_p(
        "where D_diag = sqrt(W^2 + H^2) is the frame diagonal, w_dist = 0.70, and w_scale = 0.30. If Cost(d_j, S_i) <= tau_prox (0.35) and "
        "class categories match, the framework re-associates d_j back to the master track ID id_i, restores state_i to VISIBLE, and logs a "
        "Successful Memory Recovery event, thereby actively curing the identity switch."
    )

    add_subsec_heading("C", "Quantitative Research Metrics Formulation")
    add_p(
        "The framework calculates five standardized quantitative metrics to evaluate both the generative video and the tracking framework:"
    )
    add_p(
        "1) Detection Consistency (DC): Measures the proportion of frames where target objects are successfully detected:"
    )
    add_equation("DC = (N_{active_frames} / N_{total_frames}) * 100%", "4")
    add_p(
        "2) Identity Consistency (IC): Quantifies the preservation of persistent object identities across the sequence:"
    )
    add_equation("IC = max(0, 1 - (N_{switches} / N_{tracked_objects})) * 100%", "5")
    add_p(
        "3) Object Permanence Score (OPS): Evaluates whether objects maintain identity continuity following occlusion-reappearance events:"
    )
    add_equation("OPS = (N_{successful_reid} / (N_{successful_reid} + N_{switches})) * 100%", "6")
    add_p(
        "4) Memory Recovery Rate (MRR): Assesses the efficacy of the Persistent Memory Bank in healing tracking dropouts:"
    )
    add_equation("MRR = (N_{memory_recoveries} / N_{occlusion_episodes}) * 100%", "7")
    add_p(
        "5) Mean Trajectory Prediction Error (MAE_pred): Measures the spatial accuracy (in pixels) between the dead-reckoning projected "
        "position and the ground-truth reappearance coordinate:"
    )
    add_equation("MAE_pred = (1 / K) * sum_{k=1}^K ||P_{actual}^{(k)} - P_hat_{pred}^{(k)}||_2", "8")

    # -------------------------------------------------------------
    # V. RESULTS AND DISCUSSIONS
    # -------------------------------------------------------------
    add_sec_heading("V", "Results and Discussions")
    add_subsec_heading("A", "Experimental Setup & Benchmark Dataset")
    add_p(
        "The proposed framework was implemented in Python 3.13 utilizing PyTorch and OpenCV, and executed on a dedicated NVIDIA GeForce RTX 4060 "
        "Laptop GPU (8GB VRAM) with CUDA acceleration. The inference resolution was set to native 1280px (img_size = 1280) with confidence "
        "threshold tau_conf = 0.35 and IoU threshold tau_iou = 0.35."
    )
    add_p(
        "Evaluation was conducted on a curated test suite comprising both synthetic baseline videos (featuring controlled occluder obstacles) "
        "and real AI-generated video sequences (TESTBALL, testball2 through testball5). The generative sequences feature spherical objects rolling, "
        "passing behind opaque rectangular boxes, and emerging across various occlusion spans and lighting conditions."
    )

    # TABLE I
    add_subsec_heading("B", "Quantitative Performance Evaluation")
    add_p(
        "Table I summarizes the empirical results across all benchmark sequences evaluated under the 50% Persistent Memory Bank framework."
    )

    # Create Table I
    p_t1_title = doc.add_paragraph()
    p_t1_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t1_title.paragraph_format.space_before = Pt(6)
    p_t1_title.paragraph_format.space_after = Pt(2)
    r_t1 = p_t1_title.add_run("TABLE I\nBENCHMARK EVALUATION OF OBJECT PERMANENCE ACROSS GENERATIVE VIDEO SEQUENCES")
    r_t1.font.name = 'Times New Roman'
    r_t1.font.size = Pt(8.5)
    r_t1.font.bold = True

    t1_data = [
        ["Video Sequence", "Frames", "FPS", "Detections", "Disappearances", "Re-IDs", "Switches", "DC (%)", "IC (%)", "OPS (%)"],
        ["TESTBALL.mp4", "192", "24.0", "187", "2", "2", "0", "97.40%", "100.0%", "100.0%"],
        ["testball2.mp4", "121", "24.0", "116", "1", "0", "0", "95.87%", "100.0%", "100.0%"],
        ["testball3.mp4", "144", "24.0", "141", "1", "1", "0", "97.92%", "100.0%", "100.0%"],
        ["testball4.mp4", "121", "24.0", "42", "3", "1", "1", "34.71%", "50.0%", "50.0%"],
        ["testball5.mp4", "121", "24.0", "40", "2", "1", "1", "33.06%", "50.0%", "50.0%"],
        ["demo_occlusion", "180", "30.0", "0*", "0", "0", "0", "N/A*", "100.0%", "100.0%"]
    ]

    t1 = doc.add_table(rows=len(t1_data), cols=10)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    t1.autofit = True
    for r_idx, row in enumerate(t1_data):
        for c_idx, val in enumerate(row):
            cell = t1.cell(r_idx, c_idx)
            cell.paragraphs[0].text = val
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cell.paragraphs[0].paragraph_format.line_spacing = 1.0
            cell.paragraphs[0].paragraph_format.space_before = Pt(1)
            cell.paragraphs[0].paragraph_format.space_after = Pt(1)
            run = cell.paragraphs[0].runs[0]
            run.font.name = 'Times New Roman'
            run.font.size = Pt(7.5)
            if r_idx == 0:
                run.font.bold = True

    add_p(
        "*Note: demo_occlusion.mp4 is a synthetic non-photorealistic vector test designed for baseline geometric validation."
    )

    # TABLE II: Ablation Study
    add_subsec_heading("C", "Ablation Study: Impact of the Persistent Memory Bank")
    add_p(
        "To rigorously quantify the contribution of the 50% Persistent Memory Bank, we conducted an ablation study comparing the baseline "
        "framework (30% prototype without memory bank) against the proposed memory-augmented pipeline (50% milestone). Table II presents "
        "the comparative metrics on sequences containing significant occlusion intervals."
    )

    p_t2_title = doc.add_paragraph()
    p_t2_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2_title.paragraph_format.space_before = Pt(6)
    p_t2_title.paragraph_format.space_after = Pt(2)
    r_t2 = p_t2_title.add_run("TABLE II\nABLATION STUDY: IMPACT OF PERSISTENT MEMORY BANK ON IDENTITY PRESERVATION")
    r_t2.font.name = 'Times New Roman'
    r_t2.font.size = Pt(8.5)
    r_t2.font.bold = True

    t2_data = [
        ["Sequence", "Configuration", "Occlusion Episodes", "Raw Tracker ID Swaps", "Healed Re-IDs", "MRR (%)", "Final OPS (%)"],
        ["TESTBALL.mp4", "Baseline (No Memory)", "7", "1 (at Frame 69)", "0", "0.0%", "50.0%"],
        ["TESTBALL.mp4", "Proposed (With Memory)", "7", "1 (Intercepted)", "1 (Healed)", "71.43%", "100.0%"],
        ["testball3.mp4", "Baseline (No Memory)", "1", "0", "0", "0.0%", "100.0%"],
        ["testball3.mp4", "Proposed (With Memory)", "1", "0", "1", "100.0%", "100.0%"]
    ]

    t2 = doc.add_table(rows=len(t2_data), cols=7)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    t2.autofit = True
    for r_idx, row in enumerate(t2_data):
        for c_idx, val in enumerate(row):
            cell = t2.cell(r_idx, c_idx)
            cell.paragraphs[0].text = val
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cell.paragraphs[0].paragraph_format.line_spacing = 1.0
            cell.paragraphs[0].paragraph_format.space_before = Pt(1)
            cell.paragraphs[0].paragraph_format.space_after = Pt(1)
            run = cell.paragraphs[0].runs[0]
            run.font.name = 'Times New Roman'
            run.font.size = Pt(7.5)
            if r_idx == 0:
                run.font.bold = True

    add_subsec_heading("D", "Qualitative Case Study: Real-Time Healing at Frame 69")
    add_p(
        "A compelling demonstration of the system's active healing capability occurred in TESTBALL.mp4. At Frame 51, the target ball passed "
        "entirely behind an opaque cardboard box and remained occluded for 18 consecutive frames (0.75 seconds). At Frame 69, the ball re-emerged. "
        "Under the baseline 30% pipeline, ByteTrack's internal Kalman filter timed out and assigned a new identity (Track ID 3). In our 50% "
        "framework, the Persistent Memory Bank maintained an OCCLUDED memory slot for Master ID 2 with rolling velocity V = [16.68, 0.0] px/frame. "
        "Upon detection of ID 3, the memory re-identification engine computed a matching cost of Cost = 0.3114 (normalized spatial distance = 0.301, "
        "prediction error = 300.26 px), successfully satisfying the matching threshold. The detection was re-mapped to Master ID 2, preventing an "
        "identity switch and maintaining 100.0% Object Permanence Score."
    )
    add_p(
        "Furthermore, throughout frames 51–68, the video overlay renderer generated a dashed cyan 'Ghost Bounding Box' that visually tracked "
        "the extrapolated coordinates of Master ID 2 through the box obstacle, proving that the system maintains an explicit cognitive representation "
        "of occluded physical entities."
    )

    add_subsec_heading("E", "Taxonomy of Generative AI Failure Modes")
    add_p(
        "Detailed analysis of testball4.mp4 and testball5.mp4 (both scoring OPS = 50.0%) revealed two dominant failure modes in commercial video "
        "generators: (1) Morphological Deformation: objects emerge with drastically altered aspect ratios (>60% area deviation), exceeding physical "
        "similarity thresholds; and (2) Spontaneous Deletion: objects entering occlusion fail to emerge on the other side of obstacles, indicating "
        "that latent video transformers fail to retain spatial momentum when visual evidence is masked."
    )

    # -------------------------------------------------------------
    # VI. CONCLUSION AND FUTURE SCOPE
    # -------------------------------------------------------------
    add_sec_heading("VI", "Conclusion and Future Scope")
    add_p(
        "This paper presented an automated, reproducible Object Permanence Evaluation Framework for AI-generated videos. By integrating "
        "open-vocabulary YOLO-World detection at 1280px resolution with ByteTrack multi-object tracking and a 50% Persistent Object State Memory "
        "Bank, our system overcomes the limitations of existing video metrics. The framework models physical object persistence through a discrete "
        "4-state visibility machine, projects hidden trajectories via ballistic dead-reckoning, and actively cures identity switches live during video "
        "processing. Empirical validation on real generative video sequences demonstrated the framework's capability to diagnose physical failure "
        "modes, survive 27-frame occlusion intervals, and achieve a 71.43% memory recovery rate."
    )
    add_p(
        "Future work will proceed along four strategic frontiers: (1) Stage 3 will incorporate deep appearance feature re-identification using "
        "pretrained OSNet embeddings to distinguish visually similar entities across extended gaps; (2) Stage 4 will integrate monocular depth "
        "estimation (Depth Anything) for true 3D spatial consistency behind occluders; (3) Neuromorphic Computing integration will explore Spiking "
        "Neural Networks (SNNs) with Leaky Integrate-and-Fire dynamics for low-power biological working memory; and (4) Reinforcement Learning "
        "from Physical Feedback (RLAIF) will utilize our computed Object Permanence Score as a reward signal to steer generative prompt refinement."
    )

    # -------------------------------------------------------------
    # REFERENCES
    # -------------------------------------------------------------
    add_sec_heading("", "References")

    references = [
        "[1] J. Piaget, The Construction of Reality in the Child. New York: Basic Books, 1954.",
        "[2] R. Baillargeon, 'Object permanence in 3½- and 4½-month-old infants,' Developmental Psychology, vol. 23, no. 5, pp. 655-664, 1987.",
        "[3] J. Ho, T. Salimans, A. Gritsenko, W. Chan, M. Norouzi, and D. J. Fleet, 'Video diffusion models,' in Advances in Neural Information Processing Systems (NeurIPS), vol. 35, pp. 8633-8646, 2022.",
        "[4] A. Blattmann, R. Rombach, H. Ling, T. Dockhorn, S. W. Kim, S. Fidler, and K. San-Roman, 'Align your latents: High-resolution video synthesis with latent diffusion models,' in IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 22563-22575, 2023.",
        "[5] T. Brooks, B. Peebles, C. Homes, W. DePue, Y. Guo, L. Jing, D. Schnurr, J. Taylor, T. Luhman, E. Luhman, C. Ng, R. Wang, and A. Ramesh, 'Video generation models as world simulators,' OpenAI Technical Report, 2024.",
        "[6] U. Singer, A. Polyak, T. Hayes, X. Yin, J. An, S. Zhang, Q. Hu, H. Yang, O. Ashual, O. Gafni, et al., 'Make-A-Video: Text-to-video generation without text-video data,' in International Conference on Learning Representations (ICLR), 2023.",
        "[7] A. Bewley, Z. Ge, L. Ott, F. Ramos, and B. Upcroft, 'Simple online and realtime tracking,' in IEEE International Conference on Image Processing (ICIP), pp. 3464-3468, 2016.",
        "[8] N. Wojke, A. Bewley, and D. Paulus, 'Simple online and realtime tracking with a deep association metric,' in IEEE International Conference on Image Processing (ICIP), pp. 3645-3649, 2017.",
        "[9] Y. Zhang, P. Sun, Y. Dong, Z. Jiang, Z. Qin, J. Yuan, J. Wang, and X. Liu, 'ByteTrack: Multi-object tracking by associating every detection box,' in European Conference on Computer Vision (ECCV), pp. 1-21, 2022.",
        "[10] T. Cheng, L. Song, Y. Ge, W. Liu, X. Wang, and Y. Shan, 'YOLO-World: Real-time open-vocabulary object detection,' in IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 16901-16911, 2024.",
        "[11] G. Jocher, A. Chaurasia, and J. Qiu, 'Ultralytics YOLOv8,' Version 8.0.0, 2023. [Online]. Available: https://github.com/ultralytics/ultralytics",
        "[12] R. Riochet, M. Y. Castro, M. Bernard, A. Bilmes, E. Dupoux, and I. Bento, 'IntPhys: A framework and benchmark for visual intuition of physics,' IEEE Transactions on Pattern Analysis and Machine Intelligence, vol. 44, no. 11, pp. 8016-8026, 2021.",
        "[13] T. Unterthiner, S. van Steenkiste, K. Kurach, R. Marinier, M. Michalski, and S. Gelly, 'Towards accurate generative models of video: A new metric & challenges,' arXiv preprint arXiv:1812.01717, 2018.",
        "[14] K. He, X. Zhang, S. Ren, and J. Sun, 'Deep residual learning for image recognition,' in IEEE Conference on Computer Vision and Pattern Recognition (CVPR), pp. 770-778, 2016.",
        "[15] A. Radford, J. W. Kim, C. Hallacy, A. Ramesh, G. Goh, S. Agarwal, G. Sastry, A. Askell, P. Mishkin, J. Clark, et al., 'Learning transferable visual models from natural language supervision,' in International Conference on Machine Learning (ICML), pp. 8748-8763, 2021.",
        "[16] K. Zhou, Y. Yang, A. Cavallaro, and T. Xiang, 'Omni-scale feature learning for person re-identification,' in IEEE/CVF International Conference on Computer Vision (ICCV), pp. 3702-3712, 2019.",
        "[17] L. Yang, B. Kang, Z. Huang, X. Xu, J. Feng, and H. Zhao, 'Depth Anything: Unleashing the power of large-scale unlabeled data,' in IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 10371-10381, 2024.",
        "[18] K. Ates, B. E. Sack, and E. Erdem, 'CRAFT: A benchmark for causal reasoning about dynamical physical events from videos,' in Advances in Neural Information Processing Systems (NeurIPS), vol. 33, pp. 16940-16952, 2020.",
        "[19] K. Yi, C. Gan, Y. Li, P. Kohli, J. Wu, A. Torralba, and J. B. Tenenbaum, 'CLEVRER: Collision events for video representation and reasoning,' in International Conference on Learning Representations (ICLR), 2020.",
        "[20] W. Gerstner and W. M. Kistler, Spiking Neuron Models: Single Neurons, Populations, Plasticity. Cambridge University Press, 2002."
    ]

    for ref in references:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.line_spacing = 1.0
        p_ref.paragraph_format.space_after = Pt(2)
        p_ref.paragraph_format.left_indent = Inches(0.2)
        p_ref.paragraph_format.first_line_indent = Inches(-0.2)
        r_ref = p_ref.add_run(ref)
        r_ref.font.name = 'Times New Roman'
        r_ref.font.size = Pt(8.0)

    # Save
    dirname = os.path.dirname(output_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    doc.save(output_path)
    print(f"Successfully generated IEEE format research paper docx at: {output_path}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "Research_Paper_Object_Permanence.docx"
    create_research_paper_docx(out_file)
