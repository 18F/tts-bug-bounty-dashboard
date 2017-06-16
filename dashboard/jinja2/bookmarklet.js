(() => {
  function getReportIdFromPathname() {
    const match = /\/reports\/(\d+)/.exec(window.location.pathname);
    return match && match[1];
  }

  function getReportIdFromSearch() {
    const match = /report_id=(\d+)/.exec(window.location.search);
    return match && match[1];
  }

  function getReportId() {
    return getReportIdFromPathname() || getReportIdFromSearch();
  }

  const reportId = getReportId();

  if (reportId === null) {
    window.alert(
      'This bookmarklet can only be run on Hacker One ' +
      'report detail pages.'
    );
    return;
  }

  const BASE_URL = '{{ base_url }}';
  const PATH = '{{ url("admin:dashboard_report_change", args=("1234",)) }}'
    .replace('1234', reportId);

  window.open(`${BASE_URL}${PATH}`);
})();
