# B4 属性四分类表

> **项目**：xianyunruoyou ｜ **角色**：B ｜ **任务**：B4（截止 D2）
> **版本**：v1.0（2026-09-25） ｜ **上游**：`docs/design/ontology-design.md` §3 ｜ **对齐数据源**：《美国国防部基地结构报告 FY2024》(BSR) `Federal DoD Main Report` 表
> **下游**：C3 置信度标注（每属性取值须带断言模式）、B6 实例化（A7 数据表逐字段对齐本表）、D2 SHACL（推断值禁止直写）

---

## 1. 四分类定义与判定规则

| 分类 | 定义 | 取值来源 | 本体表示 | 置信度要求 |
|---|---|---|---|---|
| **可观测特性** Measured | OSINT/官方公开文件/组委会数据**直接记载**，无需推理 | 实测（断言模式=Measured） | `xy:obs.*`，subPropertyOf `xy:MeasuredProperty` | 数据源 D-S mass + PROV-O 溯源（Ax10） |
| **功能特性** Functional | 由可观测特性**经规则推断**的功能意义 | 推断（断言模式=Inferred） | `xy:func.*`，subPropertyOf `xy:InferredProperty` | 规则输出 + 合成信任区间（Ax11） |
| **状态特性** State | 由行为函数 F 驱动、**随时间演化** | 推断/外部输入 | `xy:state.*`（对象属性→StateValue 枚举类） | 每次迁移带 StatusTransitionProcess + 时间戳 |
| **脆弱性特性** Vulnerability | 对毁伤的**敏感度/单点性**，为二级任务提供输入 | 推断 | `xy:vuln.*`，subPropertyOf `xy:InferredProperty` | 推断链溯源 + 敏感性说明 |

**判定流程**（B6 实例化时逐字段执行）：
1. 字段值能否在 BSR/OSINT 中直接读到？→ 是：Measured
2. 是否由 Measured 值经 SWRL 规则算出？→ 是：Functional 或 Vulnerability
3. 是否随外部事件（毁伤/修复/换防）变化？→ 是：State
4. 是否描述"被打击后的敏感度"？→ 是：Vulnerability

---

## 2. 属性清单（对齐 BSR 字段）

### 2.1 可观测特性（xy:obs.*，17 项）

| 本体属性 | 中文 | BSR FY2024 字段 | 数据类型 | 取值约束 | 备注 |
|---|---|---|---|---|---|
| `obs.countryRegion` | 国家/地区 | Country/State | string | 受控词表（99 值域见 A7） | 西太平洋筛选：Japan/Guam/Korea, South/Singapore/Australia/Philippines/Hawaii/Alaska |
| `obs.nearestCity` | 最近城市 | Name Nearest City | string | — | BSR 原值有前导撇号需清洗（如 `'aiea`） |
| `obs.componentType` | 设施分类 | Component | string | 受控词表：Army/Navy/Marine Corps/Air Force × Active/Guard/Reserve | 军种子类判定依据（Ax4 联动） |
| `obs.latitude` | 纬度 | （BSR 无） | decimal | [-90, 90] | **依赖 A**：A3 QGIS 坐标转换产出 |
| `obs.longitude` | 经度 | （BSR 无） | decimal | [-180, 180] | **依赖 A** |
| `obs.runwayLengthM` | 跑道长度 | （BSR 无） | integer | > 0 | **依赖 A/D**：OSINT 检索 + D5 基地说明 |
| `obs.runwayWidthM` | 跑道宽度 | （BSR 无） | integer | > 0 | 同上 |
| `obs.hardenedShelterCount` | 加固掩体数 | （BSR 无） | integer | ≥ 0 | OSINT |
| `obs.apronAreaM2` | 停机坪面积 | （BSR 无） | decimal | ≥ 0 | OSINT/影像估算（标注推断来源则降级 Inferred） |
| `obs.fuelStorageCapacityKL` | 油库容量 | （BSR 无） | decimal | ≥ 0 | OSINT |
| `obs.magazineCount` | 弹药库数 | （BSR 无） | integer | ≥ 0 | OSINT |
| `obs.aircraftCapacity` | 机位数 | （BSR 无） | integer | ≥ 0 | OSINT |
| `obs.plantReplacementValueM` | 重置价值 | Plant Replacement Value ($M) | decimal | ≥ 0 | BSR 原生，基地规模代理变量 |
| `obs.buildingOwnedCount` | 自有建筑数 | Building Owned | integer | ≥ 0 | BSR 原生 |
| `obs.buildingLeasedCount` | 租赁建筑数 | Bldgs Leased | integer | ≥ 0 | BSR 原生 |
| `obs.acresOwned` | 自有土地 | Acres Owned | decimal | ≥ 0 | BSR 原生 |
| `obs.totalAcres` | 总面积 | Total Acres | decimal | ≥ acresOwned | BSR 原生；SHACL: `sh:minInclusive acresOwned` 联动 |

> **数据覆盖缺口提示**（给 A/D 的输入）：BSR 只有 8 个基建字段，坐标与跑道等战场关键属性 **BSR 不含**，需 A 从 GIS 流程补、D 从 OSINT 补——这正是"可观测特性须附溯源"的用武之地。

### 2.2 功能特性（xy:func.*，4 项，全部推断）

| 本体属性 | 中文 | 推断规则（SWRL 草案） | 数据类型 | 取值约束 | 依赖 |
|---|---|---|---|---|---|
| `func.runwayClass` | 跑道等级 | 长度阈值分档：≥3000m→heavy-lift；≥2400m→fighter-capable；≥1800m→light-military；否则 light-civil | string | 枚举 4 值 | obs.runwayLengthM |
| `func.isMajorOperatingBase` | 主要作战基地 | PRV ≥ 中位数 ∧ aircraftCapacity ≥ 50 ∧ hasComponent 含 Runway | boolean | true/false | obs.plantReplacementValueM, obs.aircraftCapacity |
| `func.strategicValueScore` | 战略价值分 | 加权模型：0.3×PRV归一 + 0.3×机位归一 + 0.2×地理位置分 + 0.2×任务多样性 | decimal | [0,1]（SHACL 强制） | 多个 obs.* |
| `func.missionTypeSet` | 任务类型集 | 由 componentType+设施构成映射：有 PortFacility→制海；有 Runway+fighter-capable→制空… | string | 分号分隔受控词表 | obs.* + rel.hasComponent |

### 2.3 状态特性（xy:state.*，4 项）

| 本体属性 | 中文 | 取值（StateValue 枚举类） | 驱动方式 | 依赖 |
|---|---|---|---|---|
| `state.hasReadinessLevel` | 战备等级 | ReadinessHigh / ReadinessMedium / ReadinessLow | F 规则（外部条件：演习/换防/补给） | C4 规则集 |
| `state.hasOperationalStatus` | 运作状态 | Operational / Degraded / NonOperational / UnknownState | F 规则（组成成分受损状态联动，设计文档 §5.2 r1） | state.hasDamageState |
| `state.hasDamageState` | 受损状态 | Undamaged / LightDamage / SevereDamage / Destroyed | 外部事件输入 + BDA 三阶段（物理→功能→系统）评估 | C 溯源/D Brier 校准 |
| `state.isCombatCapable` | 可战性 | boolean | F 规则 r2（主跑道摧毁∧无备用→false） | **D4 失效边界焦点**：哪个条件组合会翻转本值 |

### 2.4 脆弱性特性（xy:vuln.*，4 项，全部推断）

| 本体属性 | 中文 | 计算方式 | 数据类型 | 取值约束 | 二级任务接口 |
|---|---|---|---|---|---|
| `vuln.singlePointOfFailureCount` | 单点失效源数 | hasComponent 中"仅 1 个且状态关键"的组成成分计数（如仅 1 条跑道、仅 1 座油库） | integer | ≥ 0 | aim point 候选 |
| `vuln.repairTimeEstimateHrs` | 修复时间估计 | 毁伤等级×设施类型修复系数表（工程估计） | decimal | ≥ 0 | 战役持续性评估 |
| `vuln.defenderCoverageRatio` | 防御覆盖率 | 防御系统射界覆盖/基地关键面积 | decimal | [0,1] | 突防规划输入 |
| `vuln.redundancyIndex` | 冗余指数 | 1 − (关键功能集中度)，备用跑道/油路/电源计入 | decimal | [0,1] | 体系韧性评估 |

---

## 3. 与其他角色的接口

| 接口 | 内容 | 状态 |
|---|---|---|
| → C3 | 每个属性取值须挂 `ConfidenceAnnotation`（mass/Bel/Pl/K 四值），Measured 用源质量先验、Inferred 用规则可靠度 | 本表即 C3 的属性覆盖范围 |
| → D2 | SHACL 形状：本表"取值约束"列逐条落 `validation/shapes/`（范围、[0,1] 闭区间、枚举封闭、Inferred 禁直写） | 待 D 落地 |
| ← A7 | 字段名映射：A7 CSV 列名 ↔ 本表 BSR 字段列，B6 时逐行核对 | **待 A7 交付**（D2） |
| ← D5 | OSINT 补充字段（跑道/掩体/油库）的溯源记录 | D3–D4 |

## 4. 开放问题

1. **坐标缺失**：BSR 无坐标字段，A3 的空间化流程产出前，`obs.latitude/longitude` 在 ABox 中只能以 Unknown 占位（不违反 Ax，因无 ≥1 约束）
2. **PRV 单位**：BSR 的 $M 是名义美元，跨年对比是否需通胀调整——由 D7 Brier 校准时定
3. **missionTypeSet 的受控词表**：建议与 C 协商后冻结（影响 C8 反事实查询的设计）
