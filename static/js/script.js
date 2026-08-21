document.addEventListener('DOMContentLoaded', () => {
    // Navbar
    const nav = document.querySelector('.navbar');
    const toggle = document.querySelector('.nav-toggle');
    const navMenu = document.getElementById('site-nav');
    const closeNav = document.getElementById('nav-close');

    // Scroll effect
    window.addEventListener('scroll', () => {
        nav.classList.toggle('scrolled', window.scrollY > 50);
    });

    // Mobile toggle
    if (toggle && navMenu) {
        toggle.addEventListener('click', () => {
            navMenu.classList.toggle('open');
            toggle.classList.toggle('active');
        });

        if (closeNav) {
            closeNav.addEventListener('click', () => {
                navMenu.classList.remove('open');
                toggle.classList.remove('active');
            });
        }

        navMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('open');
                toggle.classList.remove('active');
            });
        });
    }

    // Fade-in observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));

    // Contact and career forms
    const WHATSAPP_NUMBER = '5521988784497';
    const forms = document.querySelectorAll('form[data-ajax]');
    forms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = form.querySelector('button[type="submit"]');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Enviando...';

            const sendToWhatsApp = () => {
                const fd = new FormData(form);
                const linhas = [];
                fd.forEach((valor, chave) => {
                    if (chave === 'curriculo') return;
                    const v = String(valor).trim();
                    if (v) linhas.push(`${chave}: ${v}`);
                });
                const msg = 'Olá! Recebi pelo site Vida Leve:\n\n' + linhas.join('\n');
                const url = 'https://wa.me/' + WHATSAPP_NUMBER + '?text=' + encodeURIComponent(msg);
                window.open(url, '_blank', 'noopener');
                showToast('Abrindo WhatsApp para enviar sua mensagem...');
            };

            try {
                const res = await fetch(form.getAttribute('action'), {
                    method: 'POST',
                    body: new FormData(form),
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });

                let data = {};
                try {
                    data = await res.json();
                } catch (err) {
                    data = {};
                }

                if (res.ok && data.sucesso) {
                    form.reset();
                    showToast(data.mensagem || 'Enviado com sucesso!');
                } else {
                    sendToWhatsApp();
                }
            } catch (err) {
                sendToWhatsApp();
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
            }
        });
    });

    // Hero feature slider — rolagem infinita pra esquerda (direita→esquerda), sem voltar
    const slider = document.getElementById('hero-slider');
    if (slider) {
        const items = slider.querySelectorAll('.hero-feature');
        if (items.length) {
            let i = 0;
            items[0].classList.add('active');

            setInterval(() => {
                items[i].classList.remove('active');
                i = (i + 1) % items.length;
                items[i].classList.add('active');
            }, 10000);
        }
    }

    const introStoryToggle = document.getElementById('intro-story-toggle');
    const introStoryDetails = document.getElementById('intro-story-details');
    if (introStoryToggle && introStoryDetails) {
        introStoryToggle.addEventListener('click', () => {
            const isExpanded = introStoryToggle.getAttribute('aria-expanded') === 'true';
            introStoryToggle.setAttribute('aria-expanded', String(!isExpanded));
            introStoryDetails.hidden = isExpanded;
            introStoryToggle.textContent = isExpanded
                ? 'Saber mais sobre a Vida Leve'
                : 'Mostrar menos';
        });
    }
});

function showToast(msg, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = msg;
    document.body.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add('show'));

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}