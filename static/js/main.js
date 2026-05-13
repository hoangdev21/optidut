/* ══════════════════════════════════════
   MAIN.JS - JavaScript chung - OptiDUT Final Design
   ══════════════════════════════════════ */

function initApp() {
    const layout = document.querySelector('.layout');
    const sidebar = document.getElementById('sidebar');
    const toggleSidebar = document.getElementById('toggleSidebar');
    const toggleFullscreen = document.getElementById('toggleFullscreen');

    // ── Sidebar Toggle Logic ──
    if (toggleSidebar && sidebar && layout) {
        // Load state from localStorage
        const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (isCollapsed) {
            sidebar.classList.add('collapsed');
            layout.classList.add('sidebar-collapsed');
        }

        toggleSidebar.addEventListener('click', () => {
            const newState = !sidebar.classList.contains('collapsed');
            sidebar.classList.toggle('collapsed');
            layout.classList.toggle('sidebar-collapsed');
            localStorage.setItem('sidebarCollapsed', newState);
            
            // Re-trigger window resize event to fix any charts or table layouts
            window.dispatchEvent(new Event('resize'));
        });
    }

    // ── Fullscreen Logic ──
    if (toggleFullscreen) {
        toggleFullscreen.addEventListener('click', () => {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(err => {
                    console.error(`Error attempting to enable full-screen mode: ${err.message}`);
                });
                toggleFullscreen.innerHTML = "<i class='bx bx-exit-fullscreen'></i>";
            } else {
                document.exitFullscreen();
                toggleFullscreen.innerHTML = "<i class='bx bx-fullscreen'></i>";
            }
        });
    }

    // ── Auto-hide Django Messages ──
    const messages = document.querySelectorAll('.message');
    messages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-10px)';
            msg.style.transition = 'all 0.4s ease';
            setTimeout(() => msg.remove(), 400);
        }, 4000);
    });

    // ── Active Nav Link Logic (Longest Match) ──
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    let bestMatch = null;
    let maxLen = -1;

    // Clear any existing active classes first
    navLinks.forEach(link => link.classList.remove('active'));

    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (!href) return;

        // Exact match for root, or starts with for subpaths
        if (href === '/' && currentPath === '/') {
            bestMatch = link;
            maxLen = 1;
        } else if (href !== '/' && currentPath.startsWith(href)) {
            // Ensure it's a clean segment match (e.g. /equip matches /equipment/ but not /equip-ment)
            if (currentPath === href || currentPath.charAt(href.length) === '/') {
                if (href.length > maxLen) {
                    maxLen = href.length;
                    bestMatch = link;
                }
            }
        }
    });

    if (bestMatch) {
        bestMatch.classList.add('active');
    }
}

document.addEventListener('DOMContentLoaded', initApp);
