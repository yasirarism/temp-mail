const domainSelect = document.getElementById("domainSelect");
const emailInput = document.getElementById("emailInput");
const inboxDiv = document.getElementById("inbox");
const emailDetail = document.getElementById("emailDetail");
const refreshBtn = document.getElementById("refreshBtn");
const copyBtn = document.getElementById("copyBtn");

let prefix = Math.random().toString(36).substring(2, 10);
let currentDomain = "barid.site";
let currentAddress = `${prefix}@${currentDomain}`;

async function loadDomains() {
  const res = await fetch("https://api.barid.site/domains");
  const data = await res.json();
  if (data.success) {
    domainSelect.innerHTML = "";
    data.result.forEach((d) => {
      const opt = document.createElement("option");
      opt.value = d;
      opt.textContent = d;
      if (d === currentDomain) opt.selected = true;
      domainSelect.appendChild(opt);
    });
  }
}

function updateAddress() {
  currentDomain = domainSelect.value;
  currentAddress = `${prefix}@${currentDomain}`;
  emailInput.value = currentAddress;
}

async function refreshInbox() {
  inboxDiv.innerHTML = "Loading...";
  try {
    const res = await fetch(`https://api.barid.site/emails/${currentAddress}?limit=20`);
    const data = await res.json();
    if (data.success) {
      if (data.result.length === 0) {
        inboxDiv.innerHTML = "<p class='text-gray-500'>No emails yet</p>";
      } else {
        inboxDiv.innerHTML = "";
        data.result.forEach((mail) => {
          const div = document.createElement("div");
          div.className = "p-2 border rounded-lg cursor-pointer hover:bg-gray-50";
          div.innerHTML = `
            <p class="font-medium">${mail.from_address}</p>
            <p class="text-gray-600">${mail.subject}</p>
            <p class="text-xs text-gray-400">${new Date(mail.received_at * 1000).toLocaleString()}</p>
          `;
          div.onclick = () => openEmail(mail.id);
          inboxDiv.appendChild(div);
        });
      }
    }
  } catch (err) {
    inboxDiv.innerHTML = "Error loading emails";
  }
}

async function openEmail(id) {
  const res = await fetch(`https://api.barid.site/inbox/${id}`);
  const data = await res.json();
  if (data.success) {
    emailDetail.classList.remove("hidden");
    emailDetail.innerHTML = `
      <h2 class="font-bold text-lg mb-2">${data.result.subject || "(No subject)"}</h2>
      <p class="text-sm text-gray-600 mb-4">From: ${data.result.from_address}</p>
      <div class="prose max-w-none border-t pt-2">${data.result.html_content || data.result.text_content}</div>
    `;
  }
}

copyBtn.onclick = () => {
  navigator.clipboard.writeText(currentAddress);
  copyBtn.textContent = "Copied!";
  setTimeout(() => (copyBtn.textContent = "Copy"), 1500);
};

refreshBtn.onclick = refreshInbox;
domainSelect.onchange = updateAddress;

// init
updateAddress();
loadDomains().then(refreshInbox);
