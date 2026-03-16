#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"

log() {
  printf '%s\n' "$*"
}

ensure_deps() {
  log "[frontend] Installing dependencies (incl. dev)..."
  npm i --include=dev
}

run_build() {
  local log_file
  log_file="$(mktemp)"
  set +e
  (cd "${FRONTEND_DIR}" && npm run build) >"${log_file}" 2>&1
  local status=$?
  set -e
  cat "${log_file}"
  rm -f "${log_file}"
  return "${status}"
}

should_retry() {
  local file="$1"
  if rg -q "rollup-darwin-arm64" "${file}"; then
    return 0
  fi
  if rg -q "vite: command not found" "${file}"; then
    return 0
  fi
  if rg -q "Cannot find module @rollup/rollup-darwin-arm64" "${file}"; then
    return 0
  fi
  return 1
}

build_with_retry() {
  local log_file
  log_file="$(mktemp)"
  set +e
  (cd "${FRONTEND_DIR}" && npm run build) >"${log_file}" 2>&1
  local status=$?
  set -e
  cat "${log_file}"
  if [[ "${status}" -eq 0 ]]; then
    rm -f "${log_file}"
    return 0
  fi
  if should_retry "${log_file}"; then
    log "[frontend] Detected optional dependency/install issue. Cleaning and reinstalling..."
    rm -rf "${FRONTEND_DIR}/node_modules" "${FRONTEND_DIR}/package-lock.json"
    ensure_deps
    rm -f "${log_file}"
    log "[frontend] Retrying build..."
    run_build
    return $?
  fi
  rm -f "${log_file}"
  return "${status}"
}

if [[ ! -d "${FRONTEND_DIR}/node_modules" ]]; then
  ensure_deps
fi

build_with_retry
