export default function Loading() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        background:
          "radial-gradient(circle at top left, rgba(20, 184, 166, 0.18), transparent 32%), #f7f3ea",
        color: "#172126",
        fontFamily: "var(--font-display)",
        fontSize: "1.1rem",
        letterSpacing: "0.06em",
        textTransform: "uppercase",
      }}
    >
      Loading TechInsight...
    </div>
  );
}
