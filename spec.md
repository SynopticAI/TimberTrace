# TimberTrace - AI-Powered Timber Beam Reconstruction System

## Project Specification Document

**Version:** 1.0  
**Date:** November 2024  
**Project Codename:** TimberTrace

---

## 1. Project Overview

### 1.1 Background

TimberTrace is an AI-powered system designed to automatically generate CAD models and optionally CNC G-code from LiDAR point cloud scans of traditional timber roof constructions. The system aims to eliminate the labor-intensive manual measurement and CAD modeling process currently required for manufacturing replacement beams in historic building restoration.

### 1.2 Stakeholders

**Development Team:**
- **Joshua Larsch** - AI/ML Engineer, Computer Vision Specialist
  - Responsible for: ML pipeline, simulator development, overall system architecture
  - Background: Specialized in AI and computer vision

- **Father (Larsch Senior)** - Technical Advisor, Business Liaison
  - Background: Founder of ACAM (microchip design company specializing in super-precise measurement systems)
  - Role: Technical consultation, business relationship management

**Client:**
- **German Zimmermann (Master Carpenter)** - Domain Expert, Primary Stakeholder
  - Current workflow: LiDAR scanning → manual measurement → CAD modeling → CAM programming
  - Committed investment: €200,000 for development
  - Provides: Domain expertise, real-world data validation, end-user requirements

### 1.3 Problem Statement

Traditional timber roof beam replacement requires:
1. LiDAR scanning of existing beams
2. Manual measurement verification
3. Manual CAD modeling of each beam
4. CAM programming for CNC manufacturing

This process is extremely labor-intensive and time-consuming. TimberTrace automates steps 2-4.

### 1.4 Solution Overview

Two-stage AI system:
1. **Stage 1:** Automatic segmentation of individual beams from roof structure point clouds
2. **Stage 2:** Parametric extraction of beam geometry and joints
3. **Output:** CAD models (STL/STEP) and optionally CNC G-code

---

## 2. Technical Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Training Pipeline (Local)                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Procedural  │───▶│   Synthetic  │───▶│   Model      │  │
│  │  Roof Sim.   │    │   Training   │    │   Training   │  │
│  │              │    │   Data Gen.  │    │   (GPU)      │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                               │
│  Hardware: RTX 4070, AMD Ryzen 9 7950X3D, 96GB DDR5         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Inference Pipeline (Firebase)                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Flutter    │───▶│   Firebase   │───▶│  CAD Export  │  │
│  │   Frontend   │    │   Functions  │    │  STL/STEP    │  │
│  │              │    │  (CPU/GPU)   │    │  (+ G-code)  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 ML Model Architecture

**Primary Configuration:**
- **Stage 1 - Beam Segmentation:** SoftGroup
  - Size: ~40M parameters
  - Architecture: Sparse 3D U-Net with soft grouping
  - Input: Full roof structure point cloud
  - Output: Per-point instance labels (one label per beam)
  
- **Stage 2 - Parameter Extraction:** PointNeXt-S
  - Size: ~1.4M parameters
  - Architecture: Improved PointNet++ with InvResMLP blocks
  - Input: Individual beam point clouds (from Stage 1)
  - Output: Parameter vector [length, width, height, joint_type_1, joint_angle_1, ...]

**Backup Configuration:**
- Stage 1: PointGroup (~35M parameters)
- Stage 2: Point Transformer V2 (~40M parameters)

### 2.3 Training Infrastructure

**Local Development Machine:**
- GPU: NVIDIA RTX 4070 (12GB VRAM)
- CPU: AMD Ryzen 9 7950X3D (16 cores)
- RAM: 96GB DDR5
- Storage: High-speed NVMe for dataset storage
- OS: [To be determined - Linux recommended for ML workflow]

**Training Framework:**
- PyTorch with CUDA acceleration
- Mixed precision training (FP16) for efficiency
- Distributed data parallel if multi-GPU expansion needed

### 2.4 Inference Infrastructure

**Firebase Cloud Functions:**
- Primary: CPU-based inference (cost optimization)
- Fallback: GPU instances if inference time exceeds acceptable thresholds
- Alternative: Dedicated ML hosting (AWS SageMaker, GCP AI Platform) called via Firebase Functions if Firebase proves insufficient

**Expected Inference Time Targets:**
- Stage 1 (Segmentation): < 10 seconds per roof structure
- Stage 2 (Per-beam parameters): < 2 seconds per beam
- Total processing: < 2 minutes for typical roof (assuming ~20 beams)

---

## 3. Data Generation Strategy

### 3.1 Procedural Roof Simulator

**Purpose:** Generate unlimited synthetic training data with perfect ground truth labels

**Requirements:**
- Procedural generation of traditional German timber roof constructions
- Adherence to authentic roof carpentry principles and structural logic
- Variety in:
  - Roof types (gable, hip, mansard, etc.)
  - Beam dimensions
  - Joint types (mortise-tenon, lap joints, dovetails, etc.)
  - Weathering/damage patterns
  - Beam angles and orientations

**Output:**
- 3D geometry (ground truth mesh)
- Synthetic LiDAR point clouds with realistic noise
- Per-beam labels and parameters
- Metadata: joint types, dimensions, angles

**Technology Stack:**
- [To be determined: Blender Python API / Unity / Unreal Engine / Custom OpenGL]
- Point cloud generation with ray tracing or rasterization
- Noise models matching real LiDAR characteristics

### 3.2 Training Dataset Structure

**Format Options (to be finalized based on model requirements):**
- Point clouds: `.ply`, `.pcd`, or `.las` format
- Labels: JSON/HDF5 with per-point instance IDs
- Parameters: JSON/CSV with beam geometric data

**Dataset Splits:**
- Training: 70%
- Validation: 15%
- Test: 15%

**Target Dataset Size:**
- 10,000+ unique roof structures
- ~200,000+ individual beams
- Expandable as needed

### 3.3 Real Data Validation

**Phase:** After simulator implementation (Timeline Step 2)

**Process:**
1. Acquire real LiDAR scans from Zimmermann partner
2. Visual and statistical comparison with synthetic data
3. Identify and address distribution gaps
4. Iterative simulator refinement

---

## 4. Output Formats

### 4.1 Parametric Representation

**Beam Parameters (Low-Dimensional Representation):**
- Core dimensions: length, width, height (3 values)
- Position: x, y, z coordinates (3 values)
- Orientation: rotation quaternion or Euler angles (3-4 values)
- Joint 1: type (categorical), position along beam, angles (4-6 values)
- Joint 2: type (categorical), position along beam, angles (4-6 values)
- Additional joints: as needed

**Total dimensionality:** ~20-30 parameters per beam

**Joint Type Classification:**
- To be defined in consultation with Zimmermann
- Common types: mortise-tenon, lap joint, dovetail, housed joint, etc.
- Encoded as categorical variables or one-hot vectors

### 4.2 CAD Export Formats

**Primary Target: STL (Stereolithography)**
- Pros: Universal support, simple triangle mesh
- Cons: No parametric information retained
- Use case: Visual verification, basic CNC import

**Secondary Target: STEP (Standard for Exchange of Product Data)**
- Pros: Industry standard, retains parametric data, better for CAM
- Cons: More complex to generate
- Use case: Professional CAM software integration

**Generation Process:**
Parameters → Procedural mesh generation → Export to STL/STEP

### 4.3 G-code Generation (Optional Feature)

**Status:** Optional, pending discussion with Zimmermann

**Requirements:**
- CNC machine specifications (work envelope, tool library)
- Material-specific feed rates and speeds
- Safety zones and fixture considerations
- Tool path optimization

**Scope Decision Criteria:**
- Does Zimmermann use standardized CNC setup?
- Is direct G-code output valuable vs. CAM software workflow?
- Additional development time vs. core feature priority

---

## 5. User Interface

### 5.1 Platform

**Flutter-based Application**
- Cross-platform: Web app (primary) and mobile app (optional)
- Modern, responsive UI
- Real-time processing status updates

### 5.2 User Workflow

```
1. Upload LiDAR Point Cloud
   ↓
2. Processing (Firebase backend)
   - Beam segmentation
   - Parameter extraction
   - 3D visualization preview
   ↓
3. Review & Adjust (Optional)
   - Visual inspection of detected beams
   - Manual corrections if needed
   ↓
4. Export
   - Download STL/STEP files per beam
   - Optional: Download G-code
   - Generate PDF documentation
```

### 5.3 Key Features

**Input:**
- Drag-and-drop file upload
- Support for common LiDAR formats (.las, .e57, .ply, .pcd)
- Batch processing for multiple scans

**Processing:**
- Real-time progress indicators
- Estimated completion time
- Processing queue management

**Visualization:**
- 3D viewer with orbit controls
- Per-beam highlighting and selection
- Color-coded joint types
- Measurement annotations

**Export:**
- Individual beam files or complete roof package
- Organized folder structure
- Metadata CSV with beam dimensions
- Processing report PDF

### 5.4 Mobile Considerations

**Decision Point:** Depends on LiDAR scanner workflow
- If scanner has mobile connectivity → prioritize mobile app
- If scanner exports to computer → web app sufficient
- Hybrid approach: mobile for field verification, web for detailed work

---

## 6. Implementation Timeline

### Phase 1: Foundation (Weeks 1-4)
**Goal:** Implement Procedural Roof Simulator

**Tasks:**
- Research traditional German roof carpentry principles
- Design parametric roof generation system
- Implement core beam and joint geometry
- Add LiDAR simulation with realistic noise
- Generate initial synthetic dataset (1,000 roofs)

**Deliverables:**
- Working procedural simulator
- Synthetic dataset with ground truth labels
- Documentation of roof construction parameters

---

### Phase 2: Validation (Weeks 5-6)
**Goal:** Test Simulator Accuracy

**Tasks:**
- Acquire real LiDAR scans from Zimmermann
- Statistical comparison: point density, noise characteristics
- Visual comparison: joint types, beam arrangements
- Identify simulator improvements needed
- Iterate on simulator based on findings

**Deliverables:**
- Validation report comparing synthetic vs. real data
- Refined simulator with improved realism
- Expanded dataset (10,000+ roofs)

---

### Phase 3: ML Pipeline (Weeks 7-12)
**Goal:** Implement and Train ML Models

**Tasks:**
- Set up training infrastructure (PyTorch, data loaders)
- Implement SoftGroup for beam segmentation
- Train Stage 1 model on synthetic data
- Implement PointNeXt-S for parameter extraction
- Train Stage 2 model on segmented beams
- Evaluate on test set, iterate on architecture if needed
- Fine-tune with real data (if available by this point)

**Deliverables:**
- Trained Stage 1 model (segmentation)
- Trained Stage 2 model (parameter extraction)
- Evaluation metrics and performance benchmarks
- Model checkpoints and training documentation

---

### Phase 4: CAD Export (Weeks 13-14)
**Goal:** Generate STL/STEP from Parameters

**Tasks:**
- Implement parametric mesh generation from ML outputs
- Add STL export functionality
- Implement STEP export (if feasible)
- Validate geometric accuracy
- Test compatibility with common CAM software

**Deliverables:**
- STL export pipeline
- STEP export pipeline (optional, based on complexity)
- Test CAD files validated by Zimmermann

---

### Phase 5: User Interface (Weeks 15-18)
**Goal:** Create Production-Ready Flutter Application

**Tasks:**
- Design UI/UX mockups
- Implement Flutter frontend
  - File upload interface
  - 3D visualization widget
  - Processing status display
  - Export controls
- Set up Firebase backend
  - Cloud Functions for inference
  - Storage for uploaded point clouds and results
  - Authentication (if needed)
- Integrate ML models into Firebase
- End-to-end testing
- Deployment to web (and mobile if decided)

**Deliverables:**
- Production Flutter application
- Firebase backend infrastructure
- User documentation
- Demo video/presentation

---

### Phase 6: G-code Generation (Optional, Weeks 19-20)
**Goal:** Direct CNC G-code Output

**Status:** Conditional on Zimmermann requirements

**Tasks:**
- Gather CNC machine specifications
- Implement tool path generation
- Add G-code export
- Validate with Zimmermann on actual CNC

**Deliverables:**
- G-code generation module (if pursued)
- CNC-ready output files

---

## 7. Success Criteria

### 7.1 Technical Metrics

**Segmentation Accuracy:**
- IoU (Intersection over Union) > 0.85 for beam detection
- Precision/Recall > 0.90 for beam instance separation
- < 5% false negatives (missed beams)

**Parameter Extraction Accuracy:**
- Dimensional accuracy: < 5mm error for beam length/width/height
- Joint angle accuracy: < 3° error
- Joint type classification: > 95% accuracy

**Performance:**
- Full roof processing: < 2 minutes
- Inference cost: < €0.50 per roof structure

### 7.2 Business Metrics

**User Acceptance:**
- Zimmermann validates output quality as production-ready
- Time savings: > 70% reduction vs. manual workflow
- CAM compatibility: Outputs work with existing software

**Economic Viability:**
- Development completed within €200,000 budget
- Clear path to production deployment
- Scalability: System handles various roof types and sizes

### 7.3 Validation Process

1. Synthetic data evaluation (Phase 3)
2. Real scan validation with Zimmermann (Phase 2, ongoing)
3. Physical manufacturing test: Generate beams, validate CNC output
4. User testing with Zimmermann team
5. Pilot deployment on real restoration projects

---

## 8. Risk Mitigation

### 8.1 Technical Risks

**Risk:** Simulator fails to capture real-world complexity
- **Mitigation:** Early validation with real scans (Phase 2), iterative refinement

**Risk:** ML models underperform on real data despite good synthetic results
- **Mitigation:** Transfer learning, fine-tuning on small real dataset, backup model architectures

**Risk:** Point cloud noise/occlusion causes failures
- **Mitigation:** Data augmentation, robust training strategies, human-in-the-loop fallback

**Risk:** Firebase inference too slow or expensive
- **Mitigation:** Optimize models (quantization, pruning), migrate to dedicated ML hosting if needed

### 8.2 Business Risks

**Risk:** Requirements change based on Zimmermann feedback
- **Mitigation:** Modular design, iterative development with frequent demos

**Risk:** CAD/G-code output incompatible with existing workflow
- **Mitigation:** Early format validation, direct testing with CAM software

**Risk:** Budget overrun
- **Mitigation:** Phased development, MVP-first approach, optional features clearly marked

---

## 9. Future Enhancements (Post-MVP)

- Multi-material support (steel braces, connections)
- Damage assessment and repair recommendations
- Historical style classification and preservation guidelines
- Integration with BIM (Building Information Modeling) systems
- Mobile AR visualization for on-site verification
- Automated quality control reports
- Multi-language support for international markets

---

## 10. Technical Dependencies

### 10.1 Software Libraries

**Core ML:**
- PyTorch >= 2.0
- Open3D (point cloud processing)
- PyTorch3D or MinkowskiEngine (sparse convolutions)
- Hugging Face Transformers (if using pretrained backbones)

**CAD Generation:**
- Trimesh (mesh manipulation)
- Open CASCADE (STEP export)
- CadQuery or Build123d (parametric CAD Python libraries)

**Frontend:**
- Flutter >= 3.0
- Three.js or Babylon.js (3D visualization in web)
- Firebase SDK

**Backend:**
- Firebase Cloud Functions (Node.js or Python)
- Google Cloud Storage
- (Optional) ONNX Runtime for optimized inference

### 10.2 Pretrained Model Sources

- SoftGroup: [GitHub - wbhu/SoftGroup](https://github.com/thangvubk/SoftGroup)
- PointNeXt: [GitHub - guochengqian/PointNeXt](https://github.com/guochengqian/PointNeXt)
- Pretrained weights: ModelNet, ScanNet checkpoints

---

## 11. Documentation Requirements

- Architecture design documents
- Simulator parameter guide
- ML training procedures and hyperparameters
- API documentation for Firebase endpoints
- User manual for Flutter application
- CAD export format specifications
- Zimmermann collaboration notes and feedback log

---

## 12. Contact & Resources

**Project Lead:** Joshua Larsch  
**Technical Advisor:** Larsch Senior (ACAM Founder)  
**Client:** German Zimmermann (Master Carpenter)  
**Budget:** €200,000  
**Repository:** [To be created]  
**Documentation:** [To be hosted]

---

**Document Status:** Draft v1.0 - Subject to refinement based on research and stakeholder feedback

**Next Steps:**
1. Review and approve specification
2. Set up development environment
3. Begin Phase 1: Simulator implementation
4. Schedule kickoff meeting with Zimmermann for detailed requirements gathering