# iAgente_Vida - Grafo LangGraph

Generado con `graph.get_graph().draw_mermaid()`

## Diagrama Mermaid

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	orquestador(orquestador)
	needs_based_selling(needs_based_selling)
	quote(quote)
	presentador(presentador)
	__end__([<p>__end__</p>]):::last
	__start__ --> orquestador;
	orquestador -.-> __end__;
	orquestador -.-> needs_based_selling;
	orquestador -.-> presentador;
	orquestador -.-> quote;
	needs_based_selling --> __end__;
	presentador --> __end__;
	quote --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```

## Visualización Online

1. Copia el código Mermaid de arriba
2. Ve a https://mermaid.live
3. Pega el código en el editor
4. Visualiza el diagrama interactivo
