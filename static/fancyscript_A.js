function extractData() {
    const keyword = document.getElementById('keyword').value;
    const number = document.getElementById('number').value;
    const orderBy = document.getElementById("orderBy").value;

    if (!keyword || !number) {
        alert('Please fill in both fields!');
        return;
    }

    fetch(`/extract?keyword=${encodeURIComponent(keyword)}&number=${number}&orderBy=${orderBy}`)
    .then(response => {
        if (!response.ok) throw new Error("Network error");
        return response.blob();
      })
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        // Choose your own filename:
        const filename = `${keyword}_count_${number}.csv`;
        // or however you want to phrase it
        a.download = filename;
        a.click();
      })
      .catch(error => console.error('Error:', error));
}
