# java-comments

Java 注释规范 skill（Agent Skills 格式，可用于 OpenCode / Claude Code / Codex 等支持 `SKILL.md` 的 agent）。

覆盖范围：

- 类 / 接口 / 枚举注释（含 `@author`、`@since`、线程安全声明、生成代码标注）
- 方法 Javadoc（`@param` / `@return` / `@throws` / `@deprecated`、幂等与事务等业务约束）
- 字段与常量注释（单位、精度、时区、可空性、禁止魔法值）
- 行内注释与复杂逻辑说明（必须写什么、怎么写、禁止什么）
- 场景细则：MyBatis/SQL、Spring 注解方法、异常与错误码、DTO/VO、生命周期兼容、测试代码、评审、安全与保密
- 信息最小化与详略控制（保密红线：密钥/敏感业务参数禁写，只引编号；注释不写业务叙事）
- 正反例（见 [examples.md](examples.md)）与评审检查清单

面向 Spring Boot / MyBatis / JDK 17+ 的 Java 后端项目，以《阿里巴巴 Java 开发手册》注释条款为基线。

## 安装

```bash
npx skills add mo-feibai/java-comments
```

手动安装：把本仓库克隆或复制到任一 agent 全局技能目录，例如：

- OpenCode：`~/.config/opencode/skills/java-comments/` 或 `~/.agents/skills/java-comments/`
- Claude Code：`~/.claude/skills/java-comments/`

安装后新开一个会话即可生效。

## 触发方式

写、改、审查、重构 Java 代码时自动加载，或直接说：

- "按 java-comments 规范给这个类补注释"
- "Java 注释规范是什么"
- "这段复杂逻辑帮我加注释"

## 文件

| 文件 | 说明 |
| --- | --- |
| `SKILL.md` | 规范主体（总则、类/方法/字段/行内、场景细则、格式、AI 专项、检查清单） |
| `examples.md` | 9 组正反例（类、方法、字段、行内、DTO、MyBatis、复杂逻辑、安全与保密、详略控制） |
| `LICENSE` | MIT |

## License

MIT
