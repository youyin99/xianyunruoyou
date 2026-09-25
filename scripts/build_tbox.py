#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
build_tbox.py — 生成 xianyunruoyou 目标特性本体 TBox（B3 交付物）

五元组 TO = {E, A, R, Ax} 的机器可读实现，依据 docs/design/ontology-design.md v1.0：
  - E 实体集：BFO/CCO 对齐的类层次（§2）
  - A 属性集：四分类数据属性（§3）
  - R 关系集：RO/ERO 对齐对象属性（§4）
  - Ax 公理集：分部/互斥/取值/溯源完整性约束（§6）
  - 术语映射登记表（§7）→ 同步输出 mappings.ttl

产出：
  ontology/protege/xy-target-core.ttl   — 主本体（TBox，无 ABox 基地数据，合规：数据不出本地）
  ontology/axioms/mappings.ttl          — BFO/CCO/RO/PROV 映射登记表

用法：
  conda activate xianyunruoyou
  python scripts/build_tbox.py
"""

from pathlib import Path

from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD, SKOS, Literal, URIRef, BNode

# ── IRIs ────────────────────────────────────────────────────────────────────
XY = Namespace("http://xianyunruoyou.org/ontology/target#")
BFO = Namespace("http://purl.obolibrary.org/obo/BFO_")
CCO = Namespace("https://www.commoncoreontologies.org/cco#")
RO = Namespace("http://purl.obolibrary.org/obo/RO_")
ERO = Namespace("https://www.commoncoreontologies.org/ero#")
PROV = Namespace("http://www.w3.org/ns/prov#")
DCT = Namespace("http://purl.org/dc/terms/")

BASE = "http://xianyunruoyou.org/ontology/target"

OUT_CORE = Path("ontology/protege/xy-target-core.ttl")
OUT_MAP = Path("ontology/axioms/mappings.ttl")

# ── 类名速记（E 实体集） ────────────────────────────────────────────────────
MilitaryInstallation = XY.MilitaryInstallation
MilitaryBase = XY.MilitaryBase
AirBase = XY.AirBase
NavalBase = XY.NavalBase
MarineCorpsBase = XY.MarineCorpsBase
ArmyBase = XY.ArmyBase
JointBase = XY.JointBase
InstallationComponent = XY.InstallationComponent
Runway = XY.Runway
Taxiway = XY.Taxiway
AircraftShelter = XY.AircraftShelter
FuelDepot = XY.FuelDepot
MunitionsStorage = XY.MunitionsStorage
RadarStation = XY.RadarStation
AirDefensePosition = XY.AirDefensePosition
PortFacility = XY.PortFacility
CommandAndControlFacility = XY.CommandAndControlFacility
AircraftParkingApron = XY.AircraftParkingApron
DefensiveSystem = XY.DefensiveSystem
SAMBattery = XY.SAMBattery
GunsBattery = XY.GunsBattery
ElectronicWarfareSystem = XY.ElectronicWarfareSystem
OperationalActivity = XY.OperationalActivity
SortieOperation = XY.SortieOperation
LogisticsOperation = XY.LogisticsOperation
StatusTransitionProcess = XY.StatusTransitionProcess
Assertion = XY.Assertion
MeasuredAssertion = XY.MeasuredAssertion
InferredAssertion = XY.InferredAssertion
ProvenanceRecord = XY.ProvenanceRecord
ConfidenceAnnotation = XY.ConfidenceAnnotation
MeasuredProperty = XY.MeasuredProperty
InferredProperty = XY.InferredProperty
StateValue = XY.StateValue

G: Graph = Graph()  # 全局工作图，helpers 与 build_core 共用


def C(iri, label_en=None, label_zh=None, parent=None, note=None):
    """声明 OWL 类 + 标签 + 父类 + 注释。"""
    G.add((iri, RDF.type, OWL.Class))
    if label_en:
        G.add((iri, RDFS.label, Literal(label_en, lang="en")))
    if label_zh:
        G.add((iri, RDFS.label, Literal(label_zh, lang="zh")))
    if parent is not None:
        G.add((iri, RDFS.subClassOf, parent))
    if note:
        G.add((iri, RDFS.comment, Literal(note, lang="en")))


def DP(iri, label_zh, category=None, rng=None, domain=None):
    """声明数据属性；category 为 MeasuredProperty/InferredProperty（四分类挂接）。"""
    G.add((iri, RDF.type, OWL.DatatypeProperty))
    G.add((iri, RDFS.label, Literal(label_zh, lang="zh")))
    if rng is not None:
        G.add((iri, RDFS.range, rng))
    if domain is not None:
        G.add((iri, RDFS.domain, domain))
    if category is not None:
        G.add((iri, RDFS.subPropertyOf, category))


def OP(iri, label_zh, rng=None, domain=None, parent=None, inverse=None,
       transitive=False, symmetric=False):
    """声明对象属性，支持 RO/ERO 父属性、逆属性、传递/对称。"""
    G.add((iri, RDF.type, OWL.ObjectProperty))
    G.add((iri, RDFS.label, Literal(label_zh, lang="zh")))
    if rng is not None:
        G.add((iri, RDFS.range, rng))
    if domain is not None:
        G.add((iri, RDFS.domain, domain))
    if parent is not None:
        G.add((iri, RDFS.subPropertyOf, parent))
    if inverse is not None:
        G.add((iri, OWL.inverseOf, inverse))
    if transitive:
        G.add((iri, RDF.type, OWL.TransitiveProperty))
    if symmetric:
        G.add((iri, RDF.type, OWL.SymmetricProperty))


def restriction(prop, filler=None, min_card=None, exact_card=None):
    """构造限制匿名类：someValuesFrom / minQualifiedCardinality / qualifiedCardinality。"""
    r = BNode()
    G.add((r, RDF.type, OWL.Restriction))
    G.add((r, OWL.onProperty, prop))
    if exact_card is not None:
        if filler is not None:
            G.add((r, OWL.qualifiedCardinality, Literal(exact_card)))
            G.add((r, OWL.onClass, filler))
        else:
            G.add((r, OWL.cardinality, Literal(exact_card)))
    elif min_card is not None:
        if filler is not None:
            G.add((r, OWL.minQualifiedCardinality, Literal(min_card)))
            G.add((r, OWL.onClass, filler))
        else:
            G.add((r, OWL.minCardinality, Literal(min_card)))
    elif filler is not None:
        G.add((r, OWL.someValuesFrom, filler))
    return r


def disjoint(a, b):
    G.add((a, OWL.disjointWith, b))


def build_core() -> Graph:
    # ── 本体头 ──
    ontology = XY[""]
    G.add((ontology, RDF.type, OWL.Ontology))
    G.add((ontology, RDFS.label, Literal("Xianyunruoyou Target Characteristic Ontology", lang="en")))
    G.add((ontology, RDFS.label, Literal("西太平洋战区目标特性本体", lang="zh")))
    G.add((ontology, DCT.title, Literal("TO = {E, A, R, F, Ax} TBox v1.0")))
    G.add((ontology, OWL.versionIRI, URIRef(f"{BASE}/1.0")))
    G.add((ontology, RDFS.comment, Literal(
        "TBox only. No ABox/base data (compliance: organizer data stays local). "
        "Top-level anchors: BFO 2.0 / CCO v1.3 mapped via skos (see mappings.ttl).", lang="en")))

    # ════════════════════════════ E 实体集（§2） ════════════════════════════

    # —— 2.2 物质实体分支 ——
    C(MilitaryInstallation, "Military Installation", "军事设施", parent=CCO.Facility,
      note="≈ cco:Facility (BFO MaterialEntity)")
    C(MilitaryBase, "Military Base", "军事基地", parent=MilitaryInstallation,
      note="narrowMatch cco:Facility; CCO has no dedicated Base class")
    for cls, zh in [(AirBase, "空军基地"), (NavalBase, "海军基地"),
                    (MarineCorpsBase, "陆战队基地"), (ArmyBase, "陆军基地"),
                    (JointBase, "联合基地")]:
        C(cls, cls.split("#")[-1], zh, parent=MilitaryBase)

    C(InstallationComponent, "Installation Component", "设施组成", parent=MilitaryInstallation)
    for cls, zh in [(Runway, "跑道"), (Taxiway, "滑行道"), (AircraftShelter, "机库/掩体"),
                    (FuelDepot, "油库"), (MunitionsStorage, "弹药库"), (RadarStation, "雷达站"),
                    (AirDefensePosition, "防空阵地"), (PortFacility, "港口设施"),
                    (CommandAndControlFacility, "指挥设施"), (AircraftParkingApron, "停机坪")]:
        C(cls, cls.split("#")[-1], zh, parent=InstallationComponent)

    C(DefensiveSystem, "Defensive System", "防御系统装备", parent=CCO.Artifact, note="≈ cco:Artifact")
    for cls, zh in [(SAMBattery, "防空导弹连"), (GunsBattery, "高炮连"),
                    (ElectronicWarfareSystem, "电子战系统")]:
        C(cls, cls.split("#")[-1], zh, parent=DefensiveSystem)

    # —— 2.3 发生体分支 ——
    C(OperationalActivity, "Operational Activity", "作战活动",
      parent=CCO.ActOfMilitaryProcess, note="≈ cco:ActOfMilitaryProcess (BFO Process)")
    C(SortieOperation, "Sortie Operation", "架次行动", parent=OperationalActivity)
    C(LogisticsOperation, "Logistics Operation", "后勤行动", parent=OperationalActivity)
    C(StatusTransitionProcess, "Status Transition Process", "状态迁移过程",
      parent=BFO.Process, note="行为函数 F 的发生体载体")

    # —— 2.4 信息实体分支 ——
    C(Assertion, "Assertion", "断言", parent=CCO.InformationArtifact)
    C(MeasuredAssertion, "Measured Assertion", "实测断言", parent=Assertion)
    C(InferredAssertion, "Inferred Assertion", "推断断言", parent=Assertion)
    C(ProvenanceRecord, "Provenance Record", "溯源记录", parent=PROV.Entity,
      note="exactMatch prov:Entity")
    C(ConfidenceAnnotation, "Confidence Annotation", "置信度标注",
      note="Bellenger D-S pattern (arXiv:1106.3876)")

    # —— 状态枚举类（§3.2 state 前缀的取值域） ——
    C(StateValue, "State Value", "状态取值")
    for cls, zh in [(XY.ReadinessHigh, "战备-高"), (XY.ReadinessMedium, "战备-中"),
                    (XY.ReadinessLow, "战备-低"), (XY.OperationalState, "可运作"),
                    (XY.DegradedState, "降级"), (XY.NonOperationalState, "不可运作"),
                    (XY.UnknownState, "未知"), (XY.Undamaged, "未受损"),
                    (XY.LightDamage, "轻损"), (XY.SevereDamage, "重损"),
                    (XY.Destroyed, "摧毁")]:
        C(cls, cls.split("#")[-1], zh, parent=StateValue)

    # 军事组织（Ax1' 管辖约束的值域）
    C(XY.MilitaryOrganization, "Military Organization", "军事组织", parent=CCO.Agent)

    # —— 属性四分类元属性（B4 交付物的本体侧表达）——
    # 正确模式：四分类声明为**抽象超属性**（owl:DatatypeProperty），
    # 具体 obs.*/func.*/vuln.* 属性以 rdfs:subPropertyOf 挂接（RO/CCO 惯例）
    for iri, en, zh in [
        (MeasuredProperty, "Measured Property", "可观测特性(实测)"),
        (InferredProperty, "Inferred Property", "推断特性"),
    ]:
        G.add((iri, RDF.type, OWL.DatatypeProperty))
        G.add((iri, RDFS.label, Literal(en, lang="en")))
        G.add((iri, RDFS.label, Literal(zh, lang="zh")))
        G.add((iri, RDFS.comment, Literal(
            "Abstract super-property: asserted data properties MUST be sub-properties of "
            "exactly one of {MeasuredProperty, InferredProperty} (B4 four-class scheme).", lang="en")))

    # ════════════════════════════ A 属性集（§3） ════════════════════════════

    DP_OBS = [
        ("latitude", "纬度", XSD.decimal), ("longitude", "经度", XSD.decimal),
        ("runwayLengthM", "跑道长度(米)", XSD.integer), ("runwayWidthM", "跑道宽度(米)", XSD.integer),
        ("hardenedShelterCount", "加固掩体数", XSD.integer), ("apronAreaM2", "停机坪面积(m2)", XSD.decimal),
        ("fuelStorageCapacityKL", "油库容量(kL)", XSD.decimal), ("magazineCount", "弹药库数", XSD.integer),
        ("aircraftCapacity", "机位数", XSD.integer), ("countryRegion", "国家/地区", XSD.string),
        ("nearestCity", "最近城市", XSD.string), ("componentType", "设施分类(BSR)", XSD.string),
        ("plantReplacementValueM", "重置价值(百万美元)", XSD.decimal),
        ("buildingOwnedCount", "自有建筑数", XSD.integer), ("buildingLeasedCount", "租赁建筑数", XSD.integer),
        ("acresOwned", "自有土地(英亩)", XSD.decimal), ("totalAcres", "总面积(英亩)", XSD.decimal),
    ]
    for name, zh, rng in DP_OBS:
        DP(XY[f"obs.{name}"], zh, category=MeasuredProperty, rng=rng)

    DP_FUNC = [
        ("runwayClass", "跑道等级", XSD.string),
        ("isMajorOperatingBase", "主要作战基地", XSD.boolean),
        ("strategicValueScore", "战略价值分", XSD.decimal),
        ("missionTypeSet", "任务类型集", XSD.string),
    ]
    for name, zh, rng in DP_FUNC:
        DP(XY[f"func.{name}"], zh, category=InferredProperty, rng=rng)

    DP_VULN = [
        ("singlePointOfFailureCount", "单点失效源数", XSD.integer),
        ("repairTimeEstimateHrs", "修复时间估计(小时)", XSD.decimal),
        ("defenderCoverageRatio", "防御覆盖率", XSD.decimal),
        ("redundancyIndex", "冗余指数", XSD.decimal),
    ]
    for name, zh, rng in DP_VULN:
        DP(XY[f"vuln.{name}"], zh, category=InferredProperty, rng=rng)

    # 状态类数据属性（可战性为布尔，其余走状态对象属性）
    DP(XY["state.isCombatCapable"], "可战性", category=InferredProperty, rng=XSD.boolean,
       domain=MilitaryBase)

    # 实测/推断标注（B6 时逐断言声明）
    DP(XY["assertionMode"], "断言模式(Measured|Inferred)", rng=XSD.string)

    # ════════════════════════════ R 关系集（§4） ════════════════════════════
    OP(XY["rel.partOf"], "从属", domain=InstallationComponent, rng=MilitaryBase,
       parent=RO.part_of, inverse=XY["rel.hasComponent"], transitive=True)
    OP(XY["rel.hasComponent"], "组成", domain=MilitaryBase, rng=InstallationComponent,
       parent=RO.has_part, transitive=True)
    OP(XY["rel.supports"], "支撑", domain=InstallationComponent, rng=OperationalActivity,
       parent=RO.realized_in)
    OP(XY["rel.connectsTo"], "连通", domain=InstallationComponent, rng=InstallationComponent,
       parent=ERO.physically_connected_to, symmetric=True)
    OP(XY["rel.sustains"], "保障", domain=FuelDepot, rng=MilitaryBase)
    OP(XY["rel.homeportOf"], "驻泊", domain=NavalBase)
    OP(XY["rel.controlledBy"], "管辖", domain=MilitaryBase, parent=ERO.controlled_by)
    OP(XY["rel.observedBy"], "观测溯源", domain=Assertion, rng=ProvenanceRecord)

    # 状态对象属性（枚举取值域）
    OP(XY["state.hasReadinessLevel"], "战备等级", rng=StateValue, domain=MilitaryBase)
    OP(XY["state.hasOperationalStatus"], "运作状态", rng=StateValue, domain=MilitaryBase)
    OP(XY["state.hasDamageState"], "受损状态", rng=StateValue)

    # 置信度标注（§5.3 D-S 模式）
    DP(XY["confidenceMass"], "mass值", rng=XSD.decimal, domain=ConfidenceAnnotation)
    DP(XY["beliefIntervalLower"], "Bel下界", rng=XSD.decimal, domain=ConfidenceAnnotation)
    DP(XY["beliefIntervalUpper"], "Pl上界", rng=XSD.decimal, domain=ConfidenceAnnotation)
    DP(XY["conflictCoefficient"], "冲突系数K", rng=XSD.decimal, domain=ConfidenceAnnotation)
    OP(XY["hasConfidence"], "具有置信度", domain=Assertion, rng=ConfidenceAnnotation)

    # ════════════════════════════ Ax 公理集（§6） ════════════════════════════

    # Ax1 MilitaryBase ⊑ ≥1 hasComponent.InstallationComponent
    G.add((MilitaryBase, RDFS.subClassOf,
           restriction(XY["rel.hasComponent"], filler=InstallationComponent, min_card=1)))
    # Ax1' MilitaryBase ⊑ ≥1 controlledBy.MilitaryOrganization
    G.add((MilitaryBase, RDFS.subClassOf,
           restriction(XY["rel.controlledBy"], filler=XY.MilitaryOrganization, min_card=1)))
    # Ax2 Runway ⊑ ∃partOf.MilitaryBase（OWL 层）
    # 注：partOf 为传递属性，OWL 2 DL 禁止对传递属性用基数限制，
    # "恰为 1" 的完整性约束由 SHACL (validation/shapes) 强制
    G.add((Runway, RDFS.subClassOf,
           restriction(XY["rel.partOf"], filler=MilitaryBase)))
    G.add((Runway, RDFS.comment, Literal(
        "Ax2: asserted runway MUST have exactly one partOf MilitaryBase — "
        "enforced via SHACL sh:property [ sh:path xy:rel.partOf ; sh:qualifiedValueShape MilitaryBase ; sh:qualifiedMinCount 1 ; sh:qualifiedMaxCount 1 ]", lang="en")))
    # Ax7 Runway ⊑ =1 runwayLengthM（数据属性，非传递，可用基数）
    G.add((Runway, RDFS.subClassOf,
           restriction(XY["obs.runwayLengthM"], exact_card=1)))

    # Ax4 军种子类互斥（JointBase 例外：联合基地可与任何军种共存于不同个体）
    disjoint(AirBase, NavalBase)
    disjoint(AirBase, ArmyBase)
    disjoint(AirBase, MarineCorpsBase)
    disjoint(NavalBase, ArmyBase)
    disjoint(NavalBase, MarineCorpsBase)
    disjoint(ArmyBase, MarineCorpsBase)
    # Ax5 防御系统互斥
    disjoint(SAMBattery, GunsBattery)
    # Ax6 组成成分互斥（节选高频组合）
    disjoint(Runway, AircraftShelter)
    disjoint(Runway, FuelDepot)
    disjoint(Runway, MunitionsStorage)
    disjoint(FuelDepot, MunitionsStorage)
    # 断言子类互斥：实测 vs 推断
    disjoint(MeasuredAssertion, InferredAssertion)

    # Ax10 溯源完整性：Assertion ⊑ ≥1 observedBy.ProvenanceRecord
    G.add((Assertion, RDFS.subClassOf,
           restriction(XY["rel.observedBy"], filler=ProvenanceRecord, min_card=1)))
    # Ax11 推断断言必有置信度
    G.add((InferredAssertion, RDFS.subClassOf,
           restriction(XY["hasConfidence"], filler=ConfidenceAnnotation, min_card=1)))

    # Ax8 注释性约束（SHACL 落地）
    G.add((XY["func.strategicValueScore"], RDFS.comment, Literal(
        "SHACL: sh:minInclusive 0 ; sh:maxInclusive 1 (see validation/shapes)", lang="en")))

    return G


def build_mappings() -> Graph:
    """§7 术语映射登记表的机器可读版（skos:exactMatch/closeMatch/narrowMatch）。"""
    g = Graph()
    g.bind("xy", XY)
    g.bind("cco", CCO)
    g.bind("bfo", BFO)
    g.bind("ro", RO)
    g.bind("ero", ERO)
    g.bind("prov", PROV)
    g.bind("skos", SKOS)

    exact = [
        (ProvenanceRecord, PROV.Entity),
        (XY["rel.partOf"], RO.part_of),
        (XY["rel.hasComponent"], RO.has_part),
    ]
    close = [
        (MilitaryInstallation, CCO.Facility),
        (DefensiveSystem, CCO.Artifact),
        (OperationalActivity, CCO.ActOfMilitaryProcess),
        (ConfidenceAnnotation, XY.DS_Confidence),
        (XY["rel.connectsTo"], ERO.physically_connected_to),
        (XY["rel.controlledBy"], ERO.controlled_by),
        (XY["rel.supports"], RO.realized_in),
    ]
    narrow = [
        (MilitaryBase, CCO.Facility),
        (AirBase, MilitaryBase), (NavalBase, MilitaryBase),
        (MarineCorpsBase, MilitaryBase), (ArmyBase, MilitaryBase), (JointBase, MilitaryBase),
        (Runway, CCO.Facility), (Taxiway, CCO.Facility), (AircraftShelter, CCO.Facility),
        (FuelDepot, CCO.Facility), (MunitionsStorage, CCO.Facility), (RadarStation, CCO.Facility),
        (AirDefensePosition, CCO.Facility), (PortFacility, CCO.Facility),
        (CommandAndControlFacility, CCO.Facility), (AircraftParkingApron, CCO.Facility),
        (SAMBattery, DefensiveSystem), (GunsBattery, DefensiveSystem),
        (ElectronicWarfareSystem, DefensiveSystem),
        (StatusTransitionProcess, BFO.Process),
        (Assertion, CCO.InformationArtifact),
        (MeasuredAssertion, Assertion), (InferredAssertion, Assertion),
        (XY["rel.observedBy"], PROV.wasAttributedTo),
    ]
    for a, b in exact:
        g.add((a, SKOS.exactMatch, b))
    for a, b in close:
        g.add((a, SKOS.closeMatch, b))
    for a, b in narrow:
        g.add((a, SKOS.narrowMatch, b))
    return g


if __name__ == "__main__":
    core = build_core()
    OUT_CORE.parent.mkdir(parents=True, exist_ok=True)
    core.serialize(destination=str(OUT_CORE), format="turtle")
    # RDF/XML 副本：WebProtégé 上传与 owlready2/HermiT 预检用（兼容性最稳）
    out_owl = OUT_CORE.with_suffix(".owl")
    core.serialize(destination=str(out_owl), format="xml")
    print(f"[OK] core TBox  -> {OUT_CORE}  ({len(core)} triples)")
    print(f"[OK] core RDF/XML -> {out_owl}")

    mappings = build_mappings()
    OUT_MAP.parent.mkdir(parents=True, exist_ok=True)
    mappings.serialize(destination=str(OUT_MAP), format="turtle")
    print(f"[OK] mappings   -> {OUT_MAP}  ({len(mappings)} triples)")
