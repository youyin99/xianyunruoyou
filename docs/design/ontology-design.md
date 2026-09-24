# 西太平洋战区目标特性本体设计文档

> **项目**：xianyunruoyou ｜ **角色**：B｜本体建模 ｜ **任务**：B2 五元组框架设计
> **版本**：v1.0（2026-09-25） ｜ **状态**：B2 正式交付物 ｜ **维护**：B（yyvone）
> **上游依赖**：A7 基地属性数据表（B6 实例化时对齐） ｜ **下游接口**：C1–C5（置信度/溯源/规则）、D2（SHACL）

---

## 0. 设计文档的定位与读法

本文档是本体 TO = {E, A, R, F, Ax} 的**设计蓝图**，回答五个问题：

1. 实体集 E 里有什么类，层次怎么组织，哪些复用上层本体、哪些自创（§2）
2. 属性集 A 如何按四分类组织，实测与推断如何区分（§3）
3. 关系集 R 用哪些关系词，语义约束是什么（§4）
4. 行为函数 F 如何在本体中表示状态与迁移，规则接口如何留给 C（§5）
5. 公理集 Ax 用哪些完整性约束保证推理质量（§6）

配套交付物：`ontology/axioms/`（公理集条目）、`ontology/protege/`（WebProtégé 工程导出的 OWL 文件）。本文档变更需同步提交 Git（B8）。

---

## 1. 调研结论（设计依据）

### 1.1 军事本体构建

- **BFO（Basic Formal Ontology）**：ISO/IEC 21838-2 标准顶级本体，按"持续体（continuant）/发生体（occurrent）"二分组织一切实体。已被美国国防部与情报界指定为形式本体开发的基线标准。
- **CCO（Common Core Ontologies）**：基于 BFO 的 11 模块中层套件（Geospatial、Facility、Artifact、Event、Agent、Quality、Information Entity、Time、Units of Measure、Currency Unit、Extended Relation Ontology），同样被 DoD 指定为基线标准，军用与情报领域有大量成熟扩展实践。
- **决策**：**复用 BFO 2.0 + CCO 2024 年版（v1.3+）作为顶层**，不重复造轮子。自创术语限于西太平洋战区目标特性领域类，且逐条给出与 BFO/CCO 的映射（§7）。
- **风险提示**：CCO 正在做 3.0/4.0 大版本重构（引入 GeoSPARQL、QUDT），官方建议暂用 2024 稳定版。本项目锁定当前稳定版，升级留待赛后。

### 1.2 目标特性建模

- 美军联合目标工作条令（JP 3-60、AFPD 14-210 等）将目标分析组织为"目标系统 → 目标组成 → 关键元素 → 目标特性点（aim point）"的层级，每一层都关心**可观测性、功能重要性、脆弱性**三个维度。
- 目标情报的标准定义强调"刻画并定位目标组成成分，指出其**脆弱性与相对重要性**"。
- **决策**：属性四分类（可观测/功能/状态/脆弱性）与上述教义结构对齐；本体中显式建立 `TargetComponent`（组成成分）与 `AimPoint`（特性点）概念，为第二级任务留接口。

### 1.3 OWL 2 设计模式

- **RO（Relation Ontology）/ OBO 模式**：关系语义用受控词表表达（`has part`、`participates in`、`realized by`、`located in`、`derives from`），每条关系有域/值域约束与传递性等性质声明，避免自由造 `relatedTo` 一类的垃圾关系。
- **CCO 设计模式库**：官方 `design-patterns` 目录提供"以能力问题驱动、附 RDF 序列化"的模式样例，本项目按同样方法组织：**每个模式先写能力问题（CQ），再写公理**。
- **跨模块引用**：采用 OWL 2 的 `owl:imports` 分模块加载；个体与类同名时用 **punning**（如 `AirBase` 作为类与个体的双关），仅限受控场景。
- **决策**：E 集类层次 ≤ 4 层；对象属性全部挂到 RO/ERO 的父属性下；每条公理可追溯到能力问题。

### 1.4 不确定性推理

- **D-S 证据理论**：以基本概率分配（BPA/mass 函数）表达证据对命题集合的支持，用 Dempster 组合规则融合多源证据，能表达"不知道"（ignorance），比贝叶斯更适合 OSINT 多源情报融合；冲突过高时组合失效，需拒判报警——与 README 中"证据冲突过高时拒绝合成"的要求一致。
- **Bellenger & Gatepaille (2011, arXiv:1106.3876)** 给出了可导入任意领域本体的 **Dempster-Shafer 本体模式**：置信度作为断言的元数据依附于个体-属性对，配合外部 Java 推理模块消费。
- **本体 + 规则的分工**：OWL 负责静态结构与一致性，**SWRL/Drools 负责状态迁移**（F），置信度传播在规则层实现、结果写回本体标注——这是情报融合领域的通行架构。
- **决策**：采用**轻量标注路线**——置信度以 `AssertionConfidence` 标注附着在"断言"上（见 §5.3），由 C 的合成模块读写；本体自身不内置概率逻辑（PR-OWL 等超纲）。

---

## 2. 实体集 E（类层次）

命名规范：类名 PascalCase 英文；IRI 前缀 `http://xianyunruoyou.org/ontology/target#`（下称 `xy:`）。

### 2.1 顶层骨架（BFO 对齐）

```
BFO:Entity
├── BFO:Continuant（持续体）
│   ├── BFO:MaterialEntity（物质实体）
│   │   ├── BFO:ObjectAggregate
│   │   ├── BFO:Object
│   │   └── BFO:FiatObjectPart
│   └── BFO:ImmaterialEntity（不可再分空间区域等）
└── BFO:Occurrent（发生体）
    └── BFO:Process（过程）
```

### 2.2 物质实体分支（E 的主体，CCO 对齐）

```
xy:MilitaryInstallation（军事设施）           ≈ cco:Facility
├── xy:MilitaryBase（军事基地）               ≈ cco:MilitaryBase（若版本无此类则自创映射）
│   ├── xy:AirBase（空军基地）                — 自创，isa MilitaryBase
│   ├── xy:NavalBase（海军基地）              — 自创，isa MilitaryBase
│   ├── xy:MarineCorpsBase（陆战队基地）      — 自创，isa MilitaryBase
│   ├── xy:ArmyBase（陆军基地）               — 自创，isa MilitaryBase
│   └── xy:JointBase（联合基地）              — 自创，isa MilitaryBase
├── xy:InstallationComponent（设施组成）       ≈ cco:Facility + has-part 结构
│   ├── xy:Runway（跑道）                     — 自创
│   ├── xy:Taxiway（滑行道）                  — 自创
│   ├── xy:AircraftShelter / xy:Hangar（机库/掩体）— 自创
│   ├── xy:FuelDepot（油库）                  — 自创
│   ├── xy:MunitionsStorage（弹药库）         — 自创
│   ├── xy:RadarStation（雷达站）             — 自创
│   ├── xy:AirDefensePosition（防空阵地）     — 自创
│   ├── xy:PortFacility（港口设施）           — 自创（NavalBase 专用）
│   ├── xy:CommandAndControlFacility（指挥设施）— 自创
│   └── xy:AircraftParkingApron（停机坪）     — 自创
└── xy:DefensiveSystem（防御系统装备）        ≈ cco:Artifact
    ├── xy:SAMBattery（防空导弹连）
    ├── xy:GunsBattery（高炮连）
    └── xy:ElectronicWarfareSystem（电子战系统）
```

**组成关系的建模要点**（来自 pizza 练手的迁移）：`MilitaryBase` 不是按"子类"去分跑道/机库（那是 pizza 里 Margherita 之于 Pizza 的关系），而是用**对象属性 `xy:hasComponent`** 挂到 `InstallationComponent` 上——组成是关系，不是继承。这是 B3 建模时最易犯的错误，特此写明。

### 2.3 发生体分支（F 与溯源的承载）

```
BFO:Process
├── xy:OperationalActivity（作战活动）        ≈ cco:ActOfMilitaryProcess（自创映射）
│   ├── xy:SortieOperation（架次行动）
│   └── xy:LogisticsOperation（后勤行动）
└── xy:StatusTransitionProcess（状态迁移过程） — F 的发生体载体（§5）
```

### 2.4 信息实体分支（溯源与置信度的载体）

```
cco:InformationArtifact
├── xy:Assertion（断言）：一条"关于某个体某属性取某值"的主张
│   ├── xy:MeasuredAssertion（实测断言）：OSINT/组委会数据直接来源
│   └── xy:InferredAssertion（推断断言）：由规则或证据合成产出
├── xy:ProvenanceRecord（溯源记录）           ≈ prov:Entity（对齐 PROV-O，C5 使用）
└── xy:ConfidenceAnnotation（置信度标注）     — D-S 信任区间载体（§5.3）
```

### 2.5 实体集小结

- **复用类**（不重定义，直接 `owl:imports` CCO）：`Facility`、`Artifact`、`InformationArtifact`、`ActOfMilitaryProcess` 及 BFO 全部顶层类
- **自创类**：`MilitaryBase` 五军种子类、11 类设施组成、3 类防御系统、`Assertion` 系、`StatusTransitionProcess`
- **每自创类的映射声明**在 `ontology/axioms/mappings.ttl` 中逐条给出（`skos:closeMatch` / `skos:narrowMatch` 到 BFO/CCO IRI）

---

## 3. 属性集 A（四分类 + 实测/推断标记）

### 3.1 四分类定义

| 分类 | 定义 | 来源 | 示例 | OWL 表示 |
|---|---|---|---|---|
| **可观测特性** Observable | OSINT/影像/公开数据直接可采 | 实测 | 跑道长度、机库数量、坐标 | 数据属性 + `Assertion` 标注 |
| **功能特性** Functional | 由可观测特性经规则推断的功能意义 | 推断 | 跑道等级（可起降机型）、基地打击价值 | 数据属性（推断值）+ 规则溯源 |
| **状态特性** State | 由行为函数 F 驱动、随时间演化 | 推断/输入 | 战备等级、可战性、受损状态 | 状态类 + 时间戳（§5） |
| **脆弱性特性** Vulnerability | 对毁伤的敏感度，第二级输入 | 推断 | 关键节点单点性、修复时间估计 | 数据属性 + 公理约束 |

**与 pizza 的映射**：`hasCaloricContent`（数据属性）对应这里的可观测特性；`hasSpiciness some Hot`（对象属性枚举）对应状态特性的离散取值——两类模式都会用到。

### 3.2 属性清单（B6 实例化时与 A7 字段逐一对齐）

**可观测（数据属性，`xy:obs.*` 前缀）**
- `xy:obs.latitude` / `xy:obs.longitude`（decimal，WGS84，A3 坐标转换后）
- `xy:obs.runwayLengthM`（integer）、`xy:obs.runwayWidthM`（integer）
- `xy:obs.hardenedShelterCount`（integer）、`xy:obs.apronAreaM2`（decimal）
- `xy:obs.fuelStorageCapacityKL`（decimal）、`xy:obs.magazineCount`（integer）
- `xy:obs.aircraftCapacity`（integer，机位数）
- `xy:obs.countryRegion`（string）、`xy:obs.nearestCity`（string）
- `xy:obs.componentType`（string，来自 BSR 表的设施分类）
- `xy:obs.plantReplacementValueM`（decimal，PRV 价值，BSR 表原生字段）
- `xy:obs.buildingOwnedCount` / `xy:obs.buildingLeasedCount` / `xy:obs.acresOwned` / `xy:obs.totalAcres`（BSR 表原生字段）

**功能（数据属性，`xy:func.*` 前缀，全部由规则产出）**
- `xy:func.runwayClass`（string：如 " fighter-capable / heavy-lift / light-civil"）
- `xy:func.isMajorOperatingBase`（boolean）
- `xy:func.strategicValueScore`（decimal 0–1）
- `xy:func.missionTypeSet`（string 集合：制空/对海/对地/运输/侦察…）

**状态（对象属性 + 枚举类，`xy:state.*` 前缀）**
- `xy:state.hasReadinessLevel` → {`ReadinessHigh`, `ReadinessMedium`, `ReadinessLow`}
- `xy:state.hasOperationalStatus` → {`Operational`, `Degraded`, `NonOperational`, `Unknown`}
- `xy:state.hasDamageState` → {`Undamaged`, `LightDamage`, `SevereDamage`, `Destroyed`}
- `xy:state.isCombatCapable`（boolean，可战性判定，失效边界分析的焦点，D4 使用）

**脆弱性（数据属性，`xy:vuln.*` 前缀）**
- `xy:vuln.singlePointOfFailureCount`（integer）
- `xy:vuln.repairTimeEstimateHrs`（decimal）
- `xy:vuln.defenderCoverageRatio`（decimal 0–1）
- `xy:vuln.redundancyIndex`（decimal 0–1）

### 3.3 实测/推断的区分机制

- **规则**：每个数据属性必须且仅属于 {`xy:Measured`, `xy:Inferred`} 之一，通过 `xy:assertionMode` 标注声明
- **约束**：`xy:Inferred` 属性的值**禁止人工直接写入**（SHACL 校验规则，D2 落地），必须由 F 规则或证据合成产出并携带 `ConfidenceAnnotation`
- **过渡性**：一个属性可从 Inferred 升级为 Measured（如某推断值后来被影像确认），升级需在 `ProvenanceRecord` 留痕

---

## 4. 关系集 R（对象属性）

全部继承自 RO/ERO 的受控父属性，禁止自由造关系。

| 关系 | IRI | 父属性 | 域 → 值域 | 性质 | 对应教义语义 |
|---|---|---|---|---|---|
| 从属 | `xy:rel.partOf` | ro:part_of | Component → Base | 传递、反自反 | 设施组成隶属 |
| 组成 | `xy:rel.hasComponent` | ro:has_part | Base → Component | 传递 | Base 拥有 Component（`partOf` 的逆） |
| 支撑 | `xy:rel.supports` | ro:realized_in（借用） | Component → OperationalActivity | — | 设施支撑活动 |
| 连通 | `xy:rel.connectsTo` | ero:physically_connected_to | Component ↔ Component | 对称 | 跑道—滑行道—停机坪 |
| 保障 | `xy:rel.sustains` | ro:part_of（弱化） | LogisticsEntity → Base | — | 油库/弹药库对基地的保障 |
| 驻泊 | `xy:rel.homeportOf` | ro:located_in | NavalBase → Vessel | — | 第二级扩展位 |
| 管辖 | `xy:rel.controlledBy` | ero:controlled_by | Base → Agent | — | 隶属军种单位 |
| 观测 | `xy:rel.observedBy` | — | Assertion → ProvenanceRecord | — | 断言溯源挂接 |

**约束公理示例**（B5 会细化）：
- `Runway SubClassOf (xy:rel.partOf some AirBase)` — 跑道必属于某个基地
- `xy:rel.hasComponent ∘ xy:rel.partOf ≡ identity`（在同类型间）— 组成与隶属互逆
- `SAMBattery DisjointWith GunsBattery` — 防御系统子类互斥

---

## 5. 行为函数 F（状态与迁移）

### 5.1 机制选型（依据 §1.4 调研结论）

- **OWL 层**：只表达**状态的静态分类**（状态类 + 枚举对象属性）
- **规则层**：**SWRL（首选，Protégé 原生）/ Drools（备选）** 表达迁移规则，由 C 实现
- **迁移过程**：每次状态变更实例化一个 `xy:StatusTransitionProcess`，携带时间戳与触发条件记录（PROV-O 对齐）

### 5.2 状态迁移规则示例（接口约定，C 实现时扩充）

```
// r1: 跑道受损 → 基地状态降级
Base(?b) ∧ hasComponent(?b, ?r) ∧ Runway(?r) ∧ hasDamageState(?r, SevereDamage)
  → hasOperationalStatus(?b, Degraded)

// r2: 主跑道 + 无备用跑道 → 可战性失效
Base(?b) ∧ hasComponent(?b, ?r1) ∧ Runway(?r1) ∧ hasDamageState(?r1, Destroyed)
  ∧ NOT (hasComponent(?b, ?r2) ∧ Runway(?r2) ∧ hasDamageState(?r2, Undamaged))
  → isCombatCapable(?b, false)

// r3: 防御覆盖率低 → 脆弱性升高
Base(?b) ∧ defenderCoverageRatio(?b, ?c) ∧ swrlb:lessThan(?c, 0.3)
  → vuln.redundancyIndex(?b, 0.2)
```

**C 侧接口约定**：
- 输入：`ConfidenceAnnotation` 合成后的信任区间（C3/C6 产出）
- 触发：外部条件变化（如新影像证据入库）
- 输出：状态属性新值 + 新的 `StatusTransitionProcess` 个体（带 PROV-O 记录）
- 冲突处理：D-S 组合冲突系数 > 阈值（建议 0.7，最终 C 定）时**拒绝迁移并报警**，状态保持 `Unknown`

### 5.3 置信度标注模式（对齐 Bellenger D-S 本体）

```ttl
xy:Assertion  rdf:type  owl:Class .
xy:confidenceMass  rdf:type  owl:DatatypeProperty ;
    rdfs:domain  xy:ConfidenceAnnotation ;
    rdfs:range   xsd:decimal .        # 单个命题的 mass 值 [0,1]
xy:beliefIntervalLower / Upper        # Bel(a) 与 Pl(a) 区间端点
xy:conflictCoefficient                # 本次合成的冲突系数 K
```

每个 `MeasuredAssertion`/`InferredAssertion` 个体通过 `xy:rel.observedBy` 挂 `ProvenanceRecord`、通过 `xy:hasConfidence` 挂 `ConfidenceAnnotation`。**没有溯源记录的断言不进入推理**（SHACL 强制）。

---

## 6. 公理集 Ax（完整性约束，B5 的正式清单从这里取）

### 6.1 分部公理

- Ax1：`MilitaryBase ≡ MilitaryInstallation ⊓ (∃xy:rel.hasComponent ≥ 1) ∧ (∃xy:rel.controlledBy exactly 1 MilitaryOrganization)`
- Ax2：`Runway ⊑ ∃xy:rel.partOf exactly 1 MilitaryBase`（跑道唯一从属）
- Ax3：`xy:rel.hasComponent ∘ xy:rel.partOf ⊑ id`（组成-隶属互逆一致性）

### 6.2 类型互斥公理

- Ax4：`AirBase ⊓ NavalBase ⊑ ⊥`（军种子类互斥；联合基地例外走 JointBase）
- Ax5：`SAMBattery ⊓ GunsBattery ⊑ ⊥`
- Ax6：`Runway ⊓ Hangar ⊑ ⊥`（组成成分互斥）

### 6.3 取值约束公理

- Ax7：`Runway ⊑ = 1 xy:obs.runwayLengthM`（有跑道必有长度）
- Ax8：`∀b: MilitaryBase(b) → (xy:func.strategicValueScore(b) ∈ [0,1])`
- Ax9：`hasOperationalStatus 枚举 {Operational, Degraded, NonOperational, Unknown}`（封闭世界枚举，SHACL 用 sh:in 落地）

### 6.4 溯源完整性公理

- Ax10：`∀a: Assertion(a) → ∃p: ProvenanceRecord(p) ∧ xy:rel.observedBy(a, p)`（无溯源即违规）
- Ax11：`∀a: InferredAssertion(a) → xy:hasConfidence(a, ≥1 ConfidenceAnnotation)`（推断断言必有置信度）

### 6.5 能力问题（Competency Questions，验证本体的标尺）

每条公理都应服务以下 CQ，B7 一致性检查后用 CQ 做验收：

1. 列出西太平洋战区内所有可起降重型运输机的基地及其跑道长度
2. 某基地主跑道被毁后，其可战性如何变化？哪些组成成分是单点失效源？
3. 哪些基地的防空覆盖率低于阈值且战略价值高于某分值？
4. 某条断言的证据来源与合成过程是什么？置信区间多宽？
5. 两个基地之间是否存在后勤保障关系（油料/弹药互援）？

---

## 7. 术语映射登记表（BFO/CCO 对齐声明）

> 按任务要求，每个自创术语说明与上层本体的映射。完整 IRI 表在 `ontology/axioms/mappings.ttl` 维护。

| 自创术语 | 类型 | 上层本体锚点 | 匹配度 | 说明 |
|---|---|---|---|---|
| `MilitaryInstallation` | class | cco:Facility (BFO:MaterialEntity) | closeMatch | 军事用途设施 |
| `MilitaryBase` | class | cco:Facility | narrowMatch | CCO 无独立 Base 类，自创并锚定 Facility |
| `AirBase` / `NavalBase` / `MarineCorpsBase` / `ArmyBase` / `JointBase` | class | xy:MilitaryBase | narrowMatch | 军种子类，BSR 表 Component 字段可映射 |
| `Runway` / `Taxiway` / `Hangar` / `FuelDepot` / `MunitionsStorage` / `RadarStation` / `AirDefensePosition` / `PortFacility` / `CommandAndControlFacility` / `AircraftParkingApron` | class | cco:Facility + part-of 结构 | narrowMatch | 设施组成类，均为 Facility 特化 |
| `DefensiveSystem`（含 SAM/Guns/EW） | class | cco:Artifact | closeMatch | 武器装备系统 |
| `OperationalActivity` | class | cco:ActOfMilitaryProcess（BFO:Process） | closeMatch | 作战活动过程 |
| `StatusTransitionProcess` | class | BFO:Process | narrowMatch | 状态迁移专用过程类 |
| `Assertion` / `MeasuredAssertion` / `InferredAssertion` | class | cco:InformationArtifact | narrowMatch | 断言信息实体 |
| `ProvenanceRecord` | class | prov:Entity（W3C PROV-O） | exactMatch | 溯源记录，对齐 PROV-O 标准 |
| `ConfidenceAnnotation` | class | Bellenger D-S Ontology 的 Confidence | closeMatch | D-S 信任区间载体 |
| `rel.partOf` / `rel.hasComponent` | object property | ro:part_of / ro:has_part | exactMatch | 组成关系 |
| `rel.supports` | object property | ro:realized_in（语义借用） | narrowMatch | 支撑关系 |
| `rel.connectsTo` | object property | ero:physically_connected_to | closeMatch | 物理连通 |
| `rel.controlledBy` | object property | ero:controlled_by | closeMatch | 管辖关系 |
| `rel.observedBy` | object property | prov:wasAttributedTo（对齐） | narrowMatch | 断言溯源挂接 |
| `obs.*` / `func.*` / `state.*` / `vuln.*` | datatype property | cco:Quality / UnitsOfMeasure 模式 | narrowMatch | 四分类属性前缀，B6 时按 A7 字段逐一对齐 |

---

## 8. 模块化与文件组织

```
xy-target-core.ttl        # 主本体：E + A + R + Ax（导入下列模块）
xy-target-state.ttl       # 状态类 + F 的 SWRL 接口注释（C 协作）
xy-confidence.ttl         # D-S 置信度模式（C 协作）
xy-provenance.ttl         # PROV-O 对齐（C 协作）
mappings.ttl              # §7 映射登记表的机器可读版
```

- WebProtégé 托管版放置 **TBox（不含基地数据）**：`xy-target-core.ttl` 及其模块
- B6 实例化（ABox，含基地数据）**仅本地 rdflib 脚本处理**，产物不传第三方服务器（合规红线）
- 每次导出快照入 `ontology/protege/`，版本随 Git 管理

## 9. 下一步（B3–B7 路线）

| 任务 | 输入 | 产出 | 状态 |
|---|---|---|---|
| B3 建类层次/属性 | 本文档 §2 §3 §4 | WebProtégé 中的 TBox 初稿 | 待开始 |
| B4 属性四分类表 | 本文档 §3 | `docs/design/property-classification.md`（细化版） | 待开始 |
| B5 公理集 | 本文档 §6 | `ontology/axioms/` 机器可读文件 | 待开始 |
| B6 实例化 | A7 数据表 + 本文档 | ABox 三元组库（本地） | 等 A7 |
| B7 一致性检查 | B3–B5 产物 | 检查记录（HermiT 或 owlready2） | 待开始 |

---

*变更记录：v1.0（2026-09-25）B（yyvone）初版发布。*
