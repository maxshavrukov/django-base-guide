document.addEventListener("DOMContentLoaded", function () {
    const serviceSelect = document.getElementById("id_delivery_service");
    const cityGroup = document.getElementById("city_group");
    const branchGroup = document.getElementById("branch_group");
    const cityInput = document.getElementById("city_input");
    const cityRefInput = document.getElementById("city_ref");
    const citySuggestions = document.getElementById("city_suggestions");
    const addressSelect = document.getElementById("id_address");

    if (!serviceSelect) return;

    const NP_API_URL = "https://api.novaposhta.ua/v2.0/json/";

    // 1. Смена службы доставки
    serviceSelect.addEventListener("change", function () {
        const val = this.value;
        if (cityInput) cityInput.value = "";
        if (cityRefInput) cityRefInput.value = "";
        addressSelect.innerHTML = '<option value="">Сначала выберите город...</option>';
        addressSelect.disabled = true;

        if (val === "nova_poshta") {
            cityGroup.style.display = "block";
            branchGroup.style.display = "block";
            cityInput.placeholder = "Начните вводить город для Новой Почты...";
        } else if (val === "ukrposhta") {
            cityGroup.style.display = "block";
            branchGroup.style.display = "block";
            cityInput.placeholder = "Введите город или индекс Укрпошты...";
        } else if (val === "pickup") {
            cityGroup.style.display = "none";
            branchGroup.style.display = "block";
            addressSelect.disabled = false;
            addressSelect.innerHTML = '<option value="Самовывоз из магазина">Самовывоз: г. Запорожье</option>';
        }
    });

    // 2. Поиск города / отделения
    let debounceTimer;
    if (cityInput) {
        cityInput.addEventListener("input", function () {
            clearTimeout(debounceTimer);
            const query = this.value.trim();
            const service = serviceSelect.value;

            if (query.length < 2) {
                if (citySuggestions) citySuggestions.style.display = "none";
                return;
            }

            debounceTimer = setTimeout(() => {
                if (service === "nova_poshta") {
                    searchNovaPoshta(query);
                } else if (service === "ukrposhta") {
                    searchUkrposhta(query);
                }
            }, 300);
        });
    }

    // --- ЛОГИКА НОВОЙ ПОЧТЫ ---
    function searchNovaPoshta(query) {
        fetch(NP_API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                modelName: "Address",
                calledMethod: "searchSettlements",
                methodProperties: { CityName: query, Limit: "10" }
            })
        })
        .then(res => res.json())
        .then(data => {
            citySuggestions.innerHTML = "";
            if (data.success && data.data[0] && data.data[0].Addresses) {
                data.data[0].Addresses.forEach(city => {
                    const item = document.createElement("div");
                    item.className = "autocomplete_item";
                    item.textContent = city.Present;
                    item.addEventListener("click", function () {
                        cityInput.value = city.Present;
                        cityRefInput.value = city.DeliveryCity;
                        citySuggestions.style.display = "none";
                        loadNPWarehouses(city.DeliveryCity);
                    });
                    citySuggestions.appendChild(item);
                });
                citySuggestions.style.display = "block";
            }
        });
    }

    function loadNPWarehouses(cityRef) {
        addressSelect.disabled = true;
        addressSelect.innerHTML = '<option value="">Загрузка отделений...</option>';

        fetch(NP_API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                modelName: "Address",
                calledMethod: "getWarehouses",
                methodProperties: { CityRef: cityRef, Limit: "500" }
            })
        })
        .then(res => res.json())
        .then(data => {
            addressSelect.innerHTML = '<option value="" disabled selected>Выберите отделение или поштомат...</option>';
            if (data.success && data.data.length > 0) {
                data.data.forEach(wh => {
                    const opt = document.createElement("option");
                    opt.value = `НП: ${wh.Description}`;
                    opt.textContent = wh.Description;
                    addressSelect.appendChild(opt);
                });
                addressSelect.disabled = false;
            }
        });
    }

    // --- ЛОГИКА УКРПОШТЫ ---
    function searchUkrposhta(query) {
        // Открытый API-эндпоинт поиска индексов и отделений Укрпошты
        fetch(`https://postcode.in.ua/api/ukrposhta/search?q=${encodeURIComponent(query)}`)
        .then(res => {
            if (!res.ok) throw new Error();
            return res.json();
        })
        .then(data => {
            citySuggestions.innerHTML = "";
            if (data && data.length > 0) {
                data.forEach(item => {
                    const el = document.createElement("div");
                    el.className = "autocomplete_item";
                    el.textContent = `${item.city}, ${item.address} (Индекс: ${item.postcode})`;
                    el.addEventListener("click", function () {
                        cityInput.value = `${item.city} (${item.postcode})`;
                        citySuggestions.style.display = "none";

                        // Автоматически подставляем выбранное отделение в select
                        addressSelect.innerHTML = `<option value="Укрпошта: Отделение ${item.postcode}, ${item.address}" selected>Отделение №${item.postcode} (${item.address})</option>`;
                        addressSelect.disabled = false;
                    });
                    citySuggestions.appendChild(el);
                });
                citySuggestions.style.display = "block";
            }
        })
        .catch(() => {
            // Фолбэк (резервный вариант), если публичный API недоступен
            addressSelect.disabled = false;
            addressSelect.innerHTML = `
                <option value="" disabled selected>Выберите индекс / отделение...</option>
                <option value="Укрпошта: Главпочтамт (Центральное)">Центральное отделение (Главпочтамт)</option>
                <option value="Укрпошта: Доставка по индексу">Доставка по пятизначному индексу</option>
            `;
        });
    }

    // Скрытие выпадашки при клике мимо
    document.addEventListener("click", function (e) {
        if (cityInput && e.target !== cityInput && citySuggestions) {
            citySuggestions.style.display = "none";
        }
    });
});

const phoneInput = document.getElementById("id_phone");
if (phoneInput) {
    phoneInput.addEventListener("input", function () {
        // Оставляем только цифры
        this.value = this.value.replace(/\D/g, "");
    });
}