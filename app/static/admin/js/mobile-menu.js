/**
 * Mobile Menu Toggle
 * Handles hamburger menu functionality for mobile responsive design
 * Requirement: 14.5 - Collapsible navigation on mobile
 */

(function() {
    'use strict';

    // Initialize mobile menu on DOM load
    document.addEventListener('DOMContentLoaded', function() {
        initMobileMenu();
    });

    function initMobileMenu() {
        // Create hamburger menu button if it doesn't exist
        createHamburgerButton();

        // Create overlay for sidebar
        createSidebarOverlay();

        // Set up event listeners
        setupEventListeners();
    }

    function createHamburgerButton() {
        // Check if button already exists
        if (document.getElementById('mobile-menu-toggle')) {
            return;
        }

        // Create hamburger button
        const button = document.createElement('button');
        button.id = 'mobile-menu-toggle';
        button.className = 'mobile-only';
        button.setAttribute('aria-label', 'Toggle navigation menu');
        button.setAttribute('aria-expanded', 'false');
        button.innerHTML = '☰';

        // Insert at the beginning of body
        document.body.insertBefore(button, document.body.firstChild);
    }

    function createSidebarOverlay() {
        // Check if overlay already exists
        if (document.querySelector('.sidebar-overlay')) {
            return;
        }

        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.setAttribute('aria-hidden', 'true');

        // Insert after hamburger button
        const button = document.getElementById('mobile-menu-toggle');
        if (button && button.nextSibling) {
            document.body.insertBefore(overlay, button.nextSibling);
        } else {
            document.body.appendChild(overlay);
        }
    }

    function setupEventListeners() {
        const menuButton = document.getElementById('mobile-menu-toggle');
        const sidebar = document.querySelector('aside');
        const overlay = document.querySelector('.sidebar-overlay');

        if (!menuButton || !sidebar || !overlay) {
            return;
        }

        // Toggle menu on button click
        menuButton.addEventListener('click', function() {
            toggleMenu();
        });

        // Close menu on overlay click
        overlay.addEventListener('click', function() {
            closeMenu();
        });

        // Close menu on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && sidebar.classList.contains('open')) {
                closeMenu();
            }
        });

        // Close menu when clicking navigation links
        const navLinks = sidebar.querySelectorAll('a');
        navLinks.forEach(function(link) {
            link.addEventListener('click', function() {
                // Only close on mobile
                if (window.innerWidth < 768) {
                    closeMenu();
                }
            });
        });

        // Handle window resize
        let resizeTimer;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function() {
                // Close menu if resizing to desktop
                if (window.innerWidth >= 768 && sidebar.classList.contains('open')) {
                    closeMenu();
                }
            }, 250);
        });
    }

    function toggleMenu() {
        const sidebar = document.querySelector('aside');
        const overlay = document.querySelector('.sidebar-overlay');
        const menuButton = document.getElementById('mobile-menu-toggle');

        if (!sidebar || !overlay || !menuButton) {
            return;
        }

        const isOpen = sidebar.classList.contains('open');

        if (isOpen) {
            closeMenu();
        } else {
            openMenu();
        }
    }

    function openMenu() {
        const sidebar = document.querySelector('aside');
        const overlay = document.querySelector('.sidebar-overlay');
        const menuButton = document.getElementById('mobile-menu-toggle');

        if (!sidebar || !overlay || !menuButton) {
            return;
        }

        sidebar.classList.add('open');
        overlay.classList.add('active');
        menuButton.setAttribute('aria-expanded', 'true');
        menuButton.innerHTML = '✕';

        // Prevent body scroll when menu is open
        document.body.style.overflow = 'hidden';

        // Focus first link in sidebar for accessibility
        const firstLink = sidebar.querySelector('a');
        if (firstLink) {
            setTimeout(function() {
                firstLink.focus();
            }, 300); // Wait for animation
        }
    }

    function closeMenu() {
        const sidebar = document.querySelector('aside');
        const overlay = document.querySelector('.sidebar-overlay');
        const menuButton = document.getElementById('mobile-menu-toggle');

        if (!sidebar || !overlay || !menuButton) {
            return;
        }

        sidebar.classList.remove('open');
        overlay.classList.remove('active');
        menuButton.setAttribute('aria-expanded', 'false');
        menuButton.innerHTML = '☰';

        // Restore body scroll
        document.body.style.overflow = '';

        // Return focus to menu button
        menuButton.focus();
    }

    // Expose functions globally if needed
    window.MobileMenu = {
        open: openMenu,
        close: closeMenu,
        toggle: toggleMenu
    };
})();
