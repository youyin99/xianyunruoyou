# B7 前置：TBox 一致性检查记录（预演）

- **日期**：2026-09-25 ｜ **执行**：B（脚本自动化） ｜ **状态**：✅ 通过
- **对象**：`ontology/protege/xy-target-core.owl`（415 三元组 TBox，无 ABox）
- **推理机**：HermiT（owlready2 0.51 内置，JDK 17 Temurin）
- **耗时**：1.57 s ｜ **结论**：本体一致（CONSISTENT），无不可满足类

## 检查过程中发现并修复的建模错误

| # | 错误 | HermiT 报错 | 修复 |
|---|---|---|---|
| 1 | 对传递属性 `rel.partOf` 使用基数限制 | `Non-simple property 'rel.partOf' or its inverse appears in the cardinality restriction` | OWL 层降级为存在限制 ∃partOf.MilitaryBase；"恰为 1"由 SHACL `qualifiedMaxCount 1` 强制（`validation/shapes/xy-target-shapes.ttl`） |
| 2 | 数据属性被同时声明为 owl:DatatypeProperty 又 subPropertyOf 一个 owl:Class（四分类元类设计错误） | owlready2 `belongs to more than one entity types` 警告群 | 四分类改为**抽象超属性**模式：MeasuredProperty/InferredProperty 本身是 DatatypeProperty，obs.*/func.*/vuln.* 以 rdfs:subPropertyOf 挂接（RO/CCO 惯例） |

## 经验教训（供 B6/B7 正式检查参考）

1. **传递属性禁基数**是 OWL 2 DL 的硬规则——"恰好一个"类约束一律走 SHACL，OWL 只保存在在性
2. 元分类（meta-classing）慎用；属性分类用**超属性层级**表达，推理机与 SHACL 都更友好
3. owlready2 0.51 对 rdflib 生成的多行 Turtle 字面量解析有兼容问题——**交换格式用 RDF/XML**（`.owl` 副本即为此准备），Turtle 仅作人类阅读版

## 复查方式

```bash
conda activate xianyunruoyou
python scripts/build_tbox.py          # 重建 TBox
python - <<'EOF'
from owlready2 import get_ontology, sync_reasoner_hermit
import owlready2
onto = get_ontology("ontology/protege/xy-target-core.owl").load()
try:
    with onto: sync_reasoner_hermit()
    print("CONSISTENT")
except owlready2.OwlReadyInconsistentOntologyError:
    print("INCONSISTENT")
EOF
```

## SHACL 形状自检

- 形状文件：`validation/shapes/xy-target-shapes.ttl`（94 三元组，pyshacl 解析通过）
- 对当前纯 TBox 数据图校验：`conforms=True`（无 ABox 实例，符合预期）
- 覆盖公理：Ax2（跑道唯一从属）、Ax7（跑道长度）、Ax8（价值分 [0,1]）、Ax9（状态枚举封闭）、Ax10（溯源必挂）、Ax11（推断必带置信度）+ B4 取值约束（坐标范围、比率 [0,1]、推断禁直写 SPARQL 约束）
