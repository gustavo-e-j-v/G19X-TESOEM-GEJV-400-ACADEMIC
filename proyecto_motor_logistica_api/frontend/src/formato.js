// Las fechas llegan como "AAAA-MM-DD". No se usa new Date() a propósito:
// interpretaría la fecha en UTC y en México la mostraría un día antes.
export function formatearFecha(iso) {
  if (!iso) return "—";
  const [anio, mes, dia] = iso.split("-");
  return `${dia}/${mes}/${anio}`;
}

export function textoPlazo(dias) {
  if (dias < 0) {
    const n = Math.abs(dias);
    return `vencido hace ${n} día${n === 1 ? "" : "s"}`;
  }
  if (dias === 0) return "hoy";
  if (dias === 1) return "mañana";
  return `en ${dias} días`;
}

export function claseUrgencia(dias) {
  if (dias < 0) return "plazo-vencido";
  if (dias <= 2) return "plazo-cercano";
  return "plazo-ok";
}

export function textoPaquetes(n) {
  return `${n} paquete${n === 1 ? "" : "s"}`;
}
