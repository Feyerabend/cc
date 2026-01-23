
## CSS Parser in C

Assuming we already have a simple C parser that can recognise core CSS syntax and
build a basic parse tree or AST. CSS is interesting because it sits in an awkward
place between "regular" syntax and structured programming language syntax:
selectors look almost regular, declarations are structured, and extensions
(variables, nesting, mixins) push it toward a real programming language.
That makes it perfect for experimenting with where syntax ends and semantics begin.

Your projects are about turning this messy real-world language into something
more principled and analysable.

You start by treating CSS as pure syntax. Your parser builds a tree that only
represents structure: stylesheets, rules, selectors, declarations, values.
No interpretation, no validation, just form. Then each project adds one conceptual layer.


#### First project: cleaning the CST into an AST.  
You take the raw parse tree and design a real AST for CSS. You remove grammar noise,
flatten useless nodes, normalize selector structures, and decide what your "core" CSS
representation actually is. This forces you to answer what is essential structure
and what is just parsing machinery.

#### Second project: selector semantics.  
You annotate the AST with meaning for selectors. You do not execute them, but you classify
them: type selectors, class selectors, pseudo-classes, combinators. You build a semantic
model of "what kind of thing" each selector is. This shows how CSS moves from
syntax into domain-specific semantics.

#### Third project: validation pass.  
You implement a semantic checker that detects errors that grammar alone cannot:
invalid property names, invalid combinations of properties and values, duplicate declarations,
conflicting rules. This is the same role type checking plays in programming languages.

#### Fourth project: CSS variables and scope.  
You add support for custom properties (`--x`) and `var()`. You implement scoping rules
and resolution. Now your CSS AST needs symbol tables, name resolution, and environment
tracking. At this point CSS behaves like a programming language.

#### Fifth project: desugaring extensions.  
You define a small CSS extension such as nesting:
```css
.card {
  color: red;
  .title { font-weight: bold; }
}
```
You transform it into plain CSS by rewriting the AST. This shows how AST rewriting
works and how "new syntax" is usually just sugar.

#### Sixth project: intermediate representation for CSS.
You lower your AST into a normalised IR: a flat list of rules where all selectors are
explicit, all variables are resolved, and all extensions are removed. You compare your
AST and IR and see exactly when structure becomes execution-ready form.

#### Seventh project: ambiguity exploration.
You deliberately introduce ambiguous grammar constructs and study how your parser behaves.
CSS is famous for grammar hacks and recovery rules. You analyse how real-world languages
bend theoretical cleanliness.

Together these projects make CSS a laboratory for:
- syntax vs semantics,
- CST vs AST,
- AST vs IR,
- domain-specific meaning,
- and language evolution through rewriting.

You start with a "simple C parser" and end up with a miniature compiler pipeline for a
language that was never designed to be clean. That contrast is exactly what makes CSS
in this case such a powerful teaching case. Personally, I would have preferred if DSSSL
had been the choice from the beginning, but alas ..

