# Guion — eval-pipeline (demo)

## Qué decir (discurso)

> "Evaluar un sistema de IA no es pasar un solo número: es combinar señal de
> calidad con señal adversarial. Este pipeline corre dos gates independientes
> en serie: el de calidad evalúa cinco dimensiones —calidad semántica, seguridad,
> costo, latencia y gobierno— y el de red-team mide la tasa de éxito de ataques
> alineados a OWASP LLM Top 10. Si cualquiera bloquea, el release no sale."

Al mostrar el job page:

> "Gate 1 devuelve REVIEW: el sistema no está listo para producción pero tampoco
> está roto; el band de confianza lo ancla. Gate 2 devuelve NO_GO: el target de
> muestra filtra el system prompt y secreto canario, así que el pipeline
> **bloquea**, que es exactamente lo que queremos que haga un gate."

## El análisis detrás del dato

- **REVIEW del gate de calidad**: sale del *band* de confianza sobre el puntaje
  semántico (token-F1) del golden set. Se reportan tres escenarios —pesimista,
  base y optimista—, no un único número. El estado es REVIEW porque el base
  supera el umbral de REVIEW pero el pesimista no llega al de GO.
- **NO_GO del red-team**: sale del *overall ASR* (ataques exitosos / total) con
  intervalo de confianza, más reglas de tolerancia cero por severidad. El target
  de muestra es vulnerable a propósito para demostrar que el gate falla-cierra.
- **Exit codes como contrato**: 0 = no bloquea (GO/REVIEW), 1 = bloquea (NO_GO),
  2 = input inválido. El pipeline **afirma** el código esperado; si cambia, el CI
  rompe a propósito.

## Posibles preguntas y respuestas

- *¿Por qué dos repos y no uno?* Separación de responsabilidades: un equipo
  puede ser dueño de la calidad y otro de seguridad, con dueños de umbral
  distintos y ciclos de vida independientes. El pipeline los compone sin
  acoplarlos.
- **"¿Y si el target es bueno?"** El pipeline afirma el exit code esperado de la
  demo; en producción se quita la aserción y se deja que el gate bloquee el merge.
- **"¿Cuesta caro correrlo?**" No: todo es determinista, sin red y sin LLM en el
  camino crítico; los scorers son stdlib y las dependencias de runtime son cero.

## Bloqueadores / decisiones abiertas

- **`CROSS_REPO_TOKEN`**: requiere que un humano genere el PAT (Contents: read)
  sobre los dos repos privados. Sin él, el checkout cruzado falla.
- **Política de bloqueo real**: hoy el pipeline *demuestra* el bloqueo (afirma
  exit 1 en la demo). Para uso productivo, decidir si el NO_GO del red-team
  bloquea el deploy o solo abre un ticket.
- **Umbrales**: `go/review/max-cost/max-p95` y `max_overall_asr` son parámetros;
  falta acordar los valores por dominio.
