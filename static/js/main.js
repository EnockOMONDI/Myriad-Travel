/**
 * Myriad Travel - Core Interactive Client Script (Vanilla JS)
 * Handles client-side UI interactions for Django templates without React/SPA dependencies.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide icons if loaded
  if (window.lucide) {
    window.lucide.createIcons();
  }

  /* -------------------------------------------------------------------------- */
  /* 1. Currency Switching (KES <-> USD)                                        */
  /* -------------------------------------------------------------------------- */
  let currentCurrency = localStorage.getItem('myriad_currency') || 'KES';

  function setCurrency(curr) {
    currentCurrency = curr;
    localStorage.setItem('myriad_currency', curr);
    document.documentElement.setAttribute('data-currency', curr);

    const btnKes = document.getElementById('btn-currency-kes');
    const btnUsd = document.getElementById('btn-currency-usd');

    if (btnKes && btnUsd) {
      if (curr === 'KES') {
        btnKes.className = 'px-2.5 py-0.5 text-[11px] font-semibold rounded-full transition-all bg-amber-600 text-white shadow-xs';
        btnUsd.className = 'px-2.5 py-0.5 text-[11px] font-semibold rounded-full transition-all text-slate-400 hover:text-white';
      } else {
        btnUsd.className = 'px-2.5 py-0.5 text-[11px] font-semibold rounded-full transition-all bg-amber-600 text-white shadow-xs';
        btnKes.className = 'px-2.5 py-0.5 text-[11px] font-semibold rounded-full transition-all text-slate-400 hover:text-white';
      }
    }

    // Update all price tags
    document.querySelectorAll('[data-price-kes]').forEach((el) => {
      const kesVal = Number(el.getAttribute('data-price-kes') || 0);
      const usdVal = Number(el.getAttribute('data-price-usd') || 0);
      const prefix = el.getAttribute('data-price-prefix') || '';
      const suffix = el.getAttribute('data-price-suffix') || '';

      if (curr === 'KES') {
        el.textContent = `${prefix}KSh ${kesVal.toLocaleString()}${suffix}`;
      } else {
        el.textContent = `${prefix}$${usdVal.toLocaleString()}${suffix}`;
      }
    });

    // Update Lipa Pole Pole calculator after its controls have been initialized.
    window.dispatchEvent(new CustomEvent('myriad:currency-changed'));
  }

  const btnKes = document.getElementById('btn-currency-kes');
  const btnUsd = document.getElementById('btn-currency-usd');
  if (btnKes) btnKes.addEventListener('click', () => setCurrency('KES'));
  if (btnUsd) btnUsd.addEventListener('click', () => setCurrency('USD'));
  setCurrency(currentCurrency);

  /* -------------------------------------------------------------------------- */
  /* 2. Sticky Navbar Scroll Effect                                             */
  /* -------------------------------------------------------------------------- */
  const mainNav = document.getElementById('main-nav');
  window.addEventListener('scroll', () => {
    if (!mainNav) return;
    if (window.scrollY > 30) {
      mainNav.classList.add('bg-white/95', 'backdrop-blur-md', 'shadow-md', 'py-3');
      mainNav.classList.remove('bg-white', 'py-4', 'border-b', 'border-slate-100');
    } else {
      mainNav.classList.remove('bg-white/95', 'backdrop-blur-md', 'shadow-md', 'py-3');
      mainNav.classList.add('bg-white', 'py-4', 'border-b', 'border-slate-100');
    }
  });

  /* -------------------------------------------------------------------------- */
  /* 3. Mobile Navigation Drawer                                                */
  /* -------------------------------------------------------------------------- */
  const mobileMenuBtn = document.getElementById('mobile-menu-toggle-btn');
  const mobileMenuDrawer = document.getElementById('mobile-menu-drawer');
  if (mobileMenuBtn && mobileMenuDrawer) {
    mobileMenuBtn.addEventListener('click', () => {
      mobileMenuDrawer.classList.toggle('hidden');
    });
  }

  // Close mobile menu on clicking any navigation link
  document.querySelectorAll('.mobile-nav-link').forEach((link) => {
    link.addEventListener('click', () => {
      if (mobileMenuDrawer) mobileMenuDrawer.classList.add('hidden');
    });
  });

  /* -------------------------------------------------------------------------- */
  /* 4. Hero Slider Backgrounds & Tabs                                         */
  /* -------------------------------------------------------------------------- */
  const heroSlides = document.querySelectorAll('.hero-slide');
  const heroSlideBtns = document.querySelectorAll('.hero-slide-btn');
  const heroSlideTitle = document.getElementById('hero-heading');
  const heroSlideTag = document.getElementById('hero-eyebrow');
  const heroPrevBtn = document.getElementById('hero-prev-btn');
  const heroNextBtn = document.getElementById('hero-next-btn');
  let currentSlide = 0;

  function switchSlide(idx) {
    if (!heroSlides.length) return;
    heroSlides.forEach((slide, i) => {
      if (i === idx) {
        slide.classList.remove('opacity-0', 'scale-105', 'pointer-events-none');
        slide.classList.add('opacity-100', 'scale-100');
      } else {
        slide.classList.add('opacity-0', 'scale-105', 'pointer-events-none');
        slide.classList.remove('opacity-100', 'scale-100');
      }
    });

    heroSlideBtns.forEach((btn, i) => {
      if (i === idx) {
        btn.className = 'hero-slide-btn transition-all duration-300 rounded-full w-8 h-2 bg-amber-500';
      } else {
        btn.className = 'hero-slide-btn transition-all duration-300 rounded-full w-2 h-2 bg-white/40 hover:bg-white/70';
      }
    });

    const activeSlide = heroSlides[idx];
    if (activeSlide && heroSlideTitle && heroSlideTag) {
      heroSlideTitle.textContent = activeSlide.getAttribute('data-title') || '';
      heroSlideTag.textContent = activeSlide.getAttribute('data-tag') || '';
    }
    currentSlide = idx;
  }

  heroSlideBtns.forEach((btn, idx) => {
    btn.addEventListener('click', () => switchSlide(idx));
  });
  if (heroPrevBtn) {
    heroPrevBtn.addEventListener('click', () => {
      switchSlide((currentSlide - 1 + heroSlides.length) % heroSlides.length);
    });
  }
  if (heroNextBtn) {
    heroNextBtn.addEventListener('click', () => {
      switchSlide((currentSlide + 1) % heroSlides.length);
    });
  }

  if (heroSlides.length > 1) {
    setInterval(() => {
      switchSlide((currentSlide + 1) % heroSlides.length);
    }, 3000);
  }

  // Hero Search Tabs
  const heroTabs = document.querySelectorAll('.hero-tab-btn');
  const destSelect = document.getElementById('hero-search-destination');
  heroTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      heroTabs.forEach((t) => {
        t.classList.remove('bg-white', 'text-slate-900', 'shadow-md');
        t.classList.add('bg-slate-900/70', 'text-slate-300');
      });
      tab.classList.add('bg-white', 'text-slate-900', 'shadow-md');
      tab.classList.remove('bg-slate-900/70', 'text-slate-300');

      const targetType = tab.getAttribute('data-tab-type');
      if (destSelect && targetType) {
        if (targetType === 'safari') destSelect.value = 'Maasai Mara';
        else if (targetType === 'beach') destSelect.value = 'Diani Beach';
        else if (targetType === 'international') destSelect.value = 'Zanzibar';
      }
    });
  });

  /* -------------------------------------------------------------------------- */
  /* 5. Packages Category Filtering & Lipa Pole Pole Toggle                      */
  /* -------------------------------------------------------------------------- */
  let activeCategory = 'all';
  let onlyLipaPolePole = false;

  function filterPackages() {
    const cards = document.querySelectorAll('.package-card');
    let visibleCount = 0;

    cards.forEach((card) => {
      const region = card.getAttribute('data-region') || '';
      const isLipa = card.getAttribute('data-lipa') === 'true';
      const dest = (card.getAttribute('data-destination') || '').toLowerCase();
      const title = (card.getAttribute('data-title') || '').toLowerCase();

      let matchesCategory = activeCategory === 'all' || region === activeCategory;
      let matchesLipa = !onlyLipaPolePole || isLipa;

      if (matchesCategory && matchesLipa) {
        card.classList.remove('hidden');
        visibleCount++;
      } else {
        card.classList.add('hidden');
      }
    });

    const emptyState = document.getElementById('packages-empty-state');
    const packagesGrid = document.getElementById('packages-grid');
    if (emptyState && packagesGrid) {
      if (visibleCount === 0) {
        emptyState.classList.remove('hidden');
      } else {
        emptyState.classList.add('hidden');
      }
    }
  }

  document.querySelectorAll('.cat-filter-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.cat-filter-btn').forEach((b) => {
        b.className = 'cat-filter-btn whitespace-nowrap px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer bg-white hover:bg-slate-100 text-slate-700 border border-slate-200/80';
      });
      btn.className = 'cat-filter-btn whitespace-nowrap px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer bg-amber-600 text-white shadow-sm';

      activeCategory = btn.getAttribute('data-category') || 'all';
      filterPackages();
    });
  });

  const lipaToggle = document.getElementById('filter-lipa-pole-pole-toggle');
  if (lipaToggle) {
    lipaToggle.addEventListener('change', (e) => {
      onlyLipaPolePole = e.target.checked;
      filterPackages();
    });
  }

  // Handle Hero Form Submission (Scroll & Filter)
  const heroSearchForm = document.getElementById('hero-search-form');
  if (heroSearchForm) {
    heroSearchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const heroLipaCheck = document.getElementById('hero-lipa-check');
      if (heroLipaCheck && lipaToggle) {
        lipaToggle.checked = heroLipaCheck.checked;
        onlyLipaPolePole = heroLipaCheck.checked;
      }
      filterPackages();
      const pkgSection = document.getElementById('packages-section');
      if (pkgSection) pkgSection.scrollIntoView({ behavior: 'smooth' });
    });
  }

  /* -------------------------------------------------------------------------- */
  /* 6. Lipa Pole Pole Interactive Calculator                                    */
  /* -------------------------------------------------------------------------- */
  const lipaSlider = document.getElementById('lipa-budget-slider');
  const lipaBudgetDisplay = document.getElementById('lipa-budget-display');
  const lipaMonthlyDisplay = document.getElementById('lipa-monthly-display');
  const lipaDurationNote = document.getElementById('lipa-duration-note');
  const lipaDestSelect = document.getElementById('lipa-dest-select');
  const lipaWhatsAppBtn = document.getElementById('btn-start-lipa-pole-pole');
  let selectedMonths = 4;

  function updateLipaCalculator() {
    if (!lipaSlider) return;
    const isKes = currentCurrency === 'KES';
    const minVal = isKes ? 20000 : 200;
    const maxVal = isKes ? 250000 : 2500;
    const stepVal = isKes ? 5000 : 50;

    lipaSlider.min = minVal;
    lipaSlider.max = maxVal;
    lipaSlider.step = stepVal;

    let targetVal = Number(lipaSlider.value);
    if (isKes && targetVal < minVal) targetVal = 60000;
    if (!isKes && targetVal > maxVal) targetVal = 600;
    lipaSlider.value = targetVal;

    const formattedBudget = isKes ? `KSh ${targetVal.toLocaleString()}` : `$${targetVal.toLocaleString()}`;
    if (lipaBudgetDisplay) lipaBudgetDisplay.textContent = formattedBudget;

    const monthlyVal = Math.round(targetVal / selectedMonths);
    const formattedMonthly = isKes ? `KSh ${monthlyVal.toLocaleString()}` : `$${monthlyVal.toLocaleString()}`;
    if (lipaMonthlyDisplay) lipaMonthlyDisplay.textContent = formattedMonthly;

    if (lipaDurationNote) {
      lipaDurationNote.textContent = `Split across ${selectedMonths} manageable monthly payments before travel.`;
    }

    if (lipaWhatsAppBtn && lipaDestSelect) {
      const dest = lipaDestSelect.value;
      const msg = `Hello Myriad Travel, I would like to start a "Lipa Pole Pole" installment plan for ${dest}.\nTrip Estimated Budget: ${formattedBudget}\nDuration: ${selectedMonths} Months\nMonthly Contribution: ${formattedMonthly}/month\nPlease advise on account details and booking schedule.`;
      lipaWhatsAppBtn.href = `https://wa.me/254712236522?text=${encodeURIComponent(msg)}`;
    }
  }

  if (lipaSlider) {
    lipaSlider.addEventListener('input', updateLipaCalculator);
  }
  if (lipaDestSelect) {
    lipaDestSelect.addEventListener('change', updateLipaCalculator);
  }
  window.addEventListener('myriad:currency-changed', updateLipaCalculator);

  document.querySelectorAll('.lipa-month-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.lipa-month-btn').forEach((b) => {
        b.className = 'lipa-month-btn py-2 text-xs font-bold rounded-xl transition-all border cursor-pointer bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100';
      });
      btn.className = 'lipa-month-btn py-2 text-xs font-bold rounded-xl transition-all border cursor-pointer bg-emerald-600 text-white border-emerald-600 shadow-xs scale-102';

      selectedMonths = Number(btn.getAttribute('data-months') || 4);
      updateLipaCalculator();
    });
  });

  updateLipaCalculator();

  /* -------------------------------------------------------------------------- */
  /* 7. Plan My Custom Trip Modal (Multi-Step Form)                             */
  /* -------------------------------------------------------------------------- */
  const planModal = document.getElementById('plan-trip-modal');
  const openPlanBtns = document.querySelectorAll('.open-plan-modal-btn');
  const closePlanBtn = document.getElementById('close-plan-modal-btn');

  function openPlanTripModal() {
    if (planModal) planModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }

  function closePlanTripModal() {
    if (planModal) planModal.classList.add('hidden');
    document.body.style.overflow = '';
  }

  openPlanBtns.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      openPlanTripModal();
    });
  });

  if (closePlanBtn) closePlanBtn.addEventListener('click', closePlanTripModal);
  if (planModal) {
    planModal.addEventListener('click', (e) => {
      if (e.target === planModal) closePlanTripModal();
    });
  }

  // Multi-step Plan Modal Navigation
  let planStep = 1;
  const stepIndicators = document.querySelectorAll('.plan-step-indicator');
  const stepContents = document.querySelectorAll('.plan-step-content');

  function showPlanStep(stepNum) {
    planStep = stepNum;
    stepContents.forEach((el, i) => {
      if (i + 1 === stepNum) el.classList.remove('hidden');
      else el.classList.add('hidden');
    });

    stepIndicators.forEach((el, i) => {
      const circle = el.querySelector('.step-circle');
      if (i + 1 <= stepNum) {
        el.classList.add('text-amber-700');
        if (circle) circle.className = 'step-circle w-5 h-5 rounded-full flex items-center justify-center text-[10px] bg-amber-600 text-white';
      } else {
        el.classList.remove('text-amber-700');
        if (circle) circle.className = 'step-circle w-5 h-5 rounded-full flex items-center justify-center text-[10px] bg-slate-200 text-slate-600';
      }
    });
  }

  document.querySelectorAll('.plan-next-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const nextStep = Number(btn.getAttribute('data-next-step') || 2);
      showPlanStep(nextStep);
    });
  });

  document.querySelectorAll('.plan-prev-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const prevStep = Number(btn.getAttribute('data-prev-step') || 1);
      showPlanStep(prevStep);
    });
  });

  // Destination Pills Toggle in Modal
  document.querySelectorAll('.dest-pill-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      btn.classList.toggle('bg-amber-600');
      btn.classList.toggle('text-white');
      btn.classList.toggle('font-semibold');
      btn.classList.toggle('bg-slate-100');
      btn.classList.toggle('text-slate-700');
    });
  });

  // Style selector buttons in Modal
  document.querySelectorAll('.travel-style-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.travel-style-btn').forEach((b) => {
        b.className = 'travel-style-btn p-3 rounded-xl text-left border transition-all cursor-pointer bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100';
      });
      btn.className = 'travel-style-btn p-3 rounded-xl text-left border transition-all cursor-pointer bg-amber-50/80 border-amber-600 text-amber-900 shadow-xs';
    });
  });

  /* -------------------------------------------------------------------------- */
  /* 8. Package Details Itinerary Modal                                         */
  /* -------------------------------------------------------------------------- */
  const pkgModal = document.getElementById('package-detail-modal');
  const closePkgModalBtn = document.getElementById('close-package-modal-btn');

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el && value !== undefined && value !== null && value !== '') el.textContent = value;
  }

  function openPackageModal(btn) {
    if (!pkgModal) return;
    const card = btn.closest('.package-card');
    const title = btn.getAttribute('data-pkg-title') || card?.getAttribute('data-title') || 'Signature Myriad Travel Itinerary';
    const image = btn.getAttribute('data-pkg-image') || card?.querySelector('img')?.getAttribute('src') || '';
    const category = btn.getAttribute('data-pkg-category') || card?.querySelector('.absolute span')?.textContent?.trim() || 'Signature Tour';
    const duration = btn.getAttribute('data-pkg-duration') || card?.querySelector('[data-lucide="clock"]')?.parentElement?.textContent?.trim() || 'Custom Duration';
    const destination = btn.getAttribute('data-pkg-dest') || card?.getAttribute('data-destination') || 'Kenya & Beyond';
    const priceKes = Number(btn.getAttribute('data-pkg-price-kes') || card?.querySelector('[data-price-kes]')?.getAttribute('data-price-kes') || 0);
    const priceUsd = Number(btn.getAttribute('data-pkg-price-usd') || card?.querySelector('[data-price-usd]')?.getAttribute('data-price-usd') || 0);
    const lipa = (btn.getAttribute('data-pkg-lipa') || card?.getAttribute('data-lipa') || 'false') === 'true';
    const months = Number(btn.getAttribute('data-pkg-lipa-months') || 4);

    const imgEl = document.getElementById('pkg-modal-img');
    if (imgEl && image) {
      imgEl.src = image;
      imgEl.alt = title;
    }

    setText('pkg-modal-title', title);
    setText('pkg-modal-cat', category);
    setText('pkg-modal-dur', duration);
    setText('pkg-modal-dest', destination);
    setText('form-pkg-title', title);
    setText('form-pkg-name-display', title);

    const formattedKes = priceKes ? `KSh ${priceKes.toLocaleString()}` : 'Custom Quote';
    setText('pkg-modal-price', formattedKes);
    setText('pkg-modal-lipa-total', formattedKes);
    setText('pkg-modal-lipa-monthly', priceKes && months ? `KSh ${Math.round(priceKes / months).toLocaleString()} / mo` : 'Custom Plan');

    const formPkgTitle = document.getElementById('form-pkg-title');
    if (formPkgTitle) formPkgTitle.value = title;
    const lipaBadge = document.getElementById('pkg-modal-lipa-badge');
    if (lipaBadge) lipaBadge.classList.toggle('hidden', !lipa);

    pkgModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';

    const firstTab = document.querySelector('.pkg-modal-tab-btn[data-tab-target="itinerary"]');
    if (firstTab) firstTab.click();

    if (window.lucide) window.lucide.createIcons();
  }

  function closePackageModal() {
    if (pkgModal) pkgModal.classList.add('hidden');
    document.body.style.overflow = '';
  }

  document.querySelectorAll('.open-pkg-modal-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      openPackageModal(btn);
    });
  });

  document.querySelectorAll('.cat-link-trigger').forEach((link) => {
    link.addEventListener('click', () => {
      const targetCategory = link.getAttribute('data-target-category');
      if (!targetCategory) return;
      activeCategory = targetCategory;
      document.querySelectorAll('.cat-filter-btn').forEach((btn) => {
        const isActive = btn.getAttribute('data-category') === targetCategory;
        btn.className = isActive
          ? 'cat-filter-btn whitespace-nowrap px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer bg-amber-600 text-white shadow-sm'
          : 'cat-filter-btn whitespace-nowrap px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer bg-white hover:bg-slate-100 text-slate-700 border border-slate-200/80';
      });
      filterPackages();
    });
  });

  if (closePkgModalBtn) closePkgModalBtn.addEventListener('click', closePackageModal);
  if (pkgModal) {
    pkgModal.addEventListener('click', (e) => {
      if (e.target === pkgModal) closePackageModal();
    });
  }

  // Package Modal Tabs
  document.querySelectorAll('.pkg-modal-tab-btn').forEach((tab) => {
    tab.addEventListener('click', () => {
      const targetTab = tab.getAttribute('data-tab-target');

      document.querySelectorAll('.pkg-modal-tab-btn').forEach((t) => {
        t.className = 'pkg-modal-tab-btn py-3 px-4 text-xs sm:text-sm font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap border-transparent text-slate-600 hover:text-slate-900';
      });
      tab.className = 'pkg-modal-tab-btn py-3 px-4 text-xs sm:text-sm font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap border-amber-600 text-amber-700 bg-white';

      document.querySelectorAll('.pkg-modal-tab-pane').forEach((pane) => {
        if (pane.id === `pkg-pane-${targetTab}`) pane.classList.remove('hidden');
        else pane.classList.add('hidden');
      });
    });
  });

  /* -------------------------------------------------------------------------- */
  /* 9. Travel Guide Article Modal                                              */
  /* -------------------------------------------------------------------------- */
  const guideModal = document.getElementById('guide-detail-modal');
  const closeGuideBtn = document.getElementById('close-guide-modal-btn');

  window.openGuideModal = function(title, category, date, readTime, summary, pointsJson) {
    if (!guideModal) return;
    const titleEl = document.getElementById('guide-modal-title');
    const badgeEl = document.getElementById('guide-modal-badge');
    const dateEl = document.getElementById('guide-modal-date');
    const summaryEl = document.getElementById('guide-modal-summary');
    const pointsEl = document.getElementById('guide-modal-points');

    if (titleEl) titleEl.textContent = title;
    if (badgeEl) badgeEl.textContent = `${category} • ${readTime}`;
    if (dateEl) dateEl.textContent = date;
    if (summaryEl) summaryEl.textContent = summary;

    if (pointsEl && pointsJson) {
      const points = JSON.parse(pointsJson);
      pointsEl.innerHTML = points.map(pt => `
        <div class="flex items-start gap-2.5 text-xs sm:text-sm text-slate-700">
          <svg class="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
          <span>${pt}</span>
        </div>
      `).join('');
    }

    guideModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  };

  if (closeGuideBtn) {
    closeGuideBtn.addEventListener('click', () => {
      if (guideModal) guideModal.classList.add('hidden');
      document.body.style.overflow = '';
    });
  }

  // Keyboard Escape Handler
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closePlanTripModal();
      closePackageModal();
      if (guideModal) {
        guideModal.classList.add('hidden');
        document.body.style.overflow = '';
      }
    }
  });
});
