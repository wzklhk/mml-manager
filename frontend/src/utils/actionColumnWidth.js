function horizontalBoxSize(element) {
  const style = window.getComputedStyle(element);
  return (
    parseFloat(style.paddingLeft) +
    parseFloat(style.paddingRight) +
    parseFloat(style.borderLeftWidth) +
    parseFloat(style.borderRightWidth)
  );
}

export function measureActionColumnWidth(root) {
  const widths = [];
  root.querySelectorAll(".mml-row-actions").forEach((rowActions) => {
    const tableCell = rowActions.closest("td");
    const contentCell = tableCell?.querySelector(".cell");
    if (tableCell && contentCell) {
      widths.push(
        rowActions.getBoundingClientRect().width + horizontalBoxSize(contentCell) + horizontalBoxSize(tableCell),
      );
    }
  });

  const headerTitle = root.querySelector("th.actions-column-header .actions-column-title");
  const tableHeader = headerTitle?.closest("th");
  const contentHeader = headerTitle?.closest(".cell");
  if (headerTitle && tableHeader && contentHeader) {
    widths.push(
      headerTitle.getBoundingClientRect().width + horizontalBoxSize(contentHeader) + horizontalBoxSize(tableHeader),
    );
  }

  const measuredWidth = Math.ceil(Math.max(...widths));
  return Number.isFinite(measuredWidth) && measuredWidth > 0 ? measuredWidth : null;
}
