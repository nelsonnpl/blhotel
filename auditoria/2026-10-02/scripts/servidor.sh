#!/bin/sh
# servidor.sh start|stop <puerto> <perfil-bd> — pidfile, nunca pkill run.py.
# Perfiles: trabajo (artifacts/pulido/db/trabajo.sqlite, claves en blanco por
# entorno) | be (copia propia del carril BE) | operativa (solo ventanas F0.5/F1B).
# Uso: sh servidor.sh start 5060 trabajo  |  sh servidor.sh stop 5060
set -eu
CMD="${1:-}"; PORT="${2:-}"; PERFIL="${3:-trabajo}"
PIDF="/tmp/atlas-pulido-${PORT}.pid"
case "$CMD" in
  start)
    if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then
      echo "YA pid $(cat "$PIDF") en :$PORT"; exit 0
    fi
    case "$PERFIL" in
      trabajo) export SQLITE_PATH="./artifacts/pulido/db/trabajo.sqlite"
        export OPENROUTER_API_KEY="" SERPAPI_API_KEY="" DECODO_USERNAME="" DECODO_PASSWORD="" DECODO_TOKEN="";;
      be) export SQLITE_PATH="./artifacts/pulido/db/be.sqlite";;
      operativa) export SQLITE_PATH="./data/booking-prices.sqlite";;
      *) echo "perfil $PERFIL (trabajo|be|operativa)"; exit 1;;
    esac
    nohup env FLASK_PORT="$PORT" .venv/bin/python run.py > "/tmp/atlas-pulido-${PORT}.log" 2>&1 &
    echo $! > "$PIDF"
    echo "OK pid $! en :$PORT perfil $PERFIL"
    ;;
  stop)
    [ -f "$PIDF" ] || { echo "no hay pidfile :$PORT"; exit 0; }
    PID="$(cat "$PIDF")"
    kill "$PID" 2>/dev/null || true
    for i in 1 2 3 4 5 6 7 8 9 10; do kill -0 "$PID" 2>/dev/null || break; sleep 1; done
    kill -0 "$PID" 2>/dev/null && { echo "MAL sigue $PID"; exit 1; }
    rm -f "$PIDF"; echo "OK parado :$PORT"
    ;;
  *) echo "uso: servidor.sh start|stop <puerto> [perfil]"; exit 1;;
esac
