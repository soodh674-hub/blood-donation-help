// Advanced AOS Animations for BloodLife Platform

document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-out-cubic',
            once: true,
            offset: 100,
            delay: 0
        });
    } else {
        console.warn('AOS not loaded');
        return;
    }

    // Hero Section Animations
    function initHeroAnimations() {
        const hero = document.querySelector('.hero');
        if (!hero) return;

        // Add AOS data attributes to hero elements
        const heroContent = document.querySelector('.hero-content');
        if (heroContent) {
            heroContent.setAttribute('data-aos', 'fade-up');
            heroContent.setAttribute('data-aos-duration', '1000');
            heroContent.setAttribute('data-aos-delay', '100');
        }

        const heroMedia = document.querySelector('.hero-media-card');
        if (heroMedia) {
            heroMedia.setAttribute('data-aos', 'fade-left');
            heroMedia.setAttribute('data-aos-duration', '1200');
            heroMedia.setAttribute('data-aos-delay', '300');
        }

        // Refresh AOS after adding attributes
        if (typeof AOS !== 'undefined') {
            AOS.refresh();
        }
    }

    // Story Block Animations
    function initStoryAnimations() {
        // Add AOS to story points
        const storyPoints = document.querySelectorAll('.story-point');
        storyPoints.forEach((point, i) => {
            point.setAttribute('data-aos', 'fade-up');
            point.setAttribute('data-aos-delay', (i * 100).toString());
        });

        // Add AOS to steps
        const steps = document.querySelectorAll('.steps > li');
        steps.forEach((step, i) => {
            step.setAttribute('data-aos', 'fade-right');
            step.setAttribute('data-aos-delay', (i * 150).toString());
        });

        // Add AOS to media cards
        const mediaCards = document.querySelectorAll('.story-media .rounded-2xl');
        mediaCards.forEach((card, i) => {
            card.setAttribute('data-aos', 'fade-up');
            card.setAttribute('data-aos-delay', (i * 100).toString());
        });

        if (typeof AOS !== 'undefined') {
            AOS.refresh();
        }
    }

    // Impact Section Animations
    function initImpactAnimations() {
        // Animated counters with AOS
        const counters = document.querySelectorAll('.impact-number');
        counters.forEach(counter => {
            const target = parseInt(counter.getAttribute('data-count-to')) || 0;
            
            counter.setAttribute('data-aos', 'fade-up');
            counter.setAttribute('data-aos-once', 'true');
            
            counter.addEventListener('aos:in', () => {
                animateCounter(counter, target);
            });
        });

        // Impact cards entrance
        const impactCards = document.querySelectorAll('.impact-card');
        impactCards.forEach((card, i) => {
            card.setAttribute('data-aos', 'zoom-in');
            card.setAttribute('data-aos-delay', (i * 100).toString());
        });

        if (typeof AOS !== 'undefined') {
            AOS.refresh();
        }
    }

    // Counter animation function
    function animateCounter(element, target) {
        const duration = 2000; // 2 seconds
        const increment = target / (duration / 16); // 60fps
        let current = 0;
        
        const updateCounter = () => {
            current += increment;
            if (current < target) {
                element.textContent = Math.floor(current);
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = target;
            }
        };
        
        updateCounter();
    }

    // Form Animations
    function initFormAnimations() {
        // Add AOS to form steps
        const steps = document.querySelectorAll('#donor-registration-form .step');
        steps.forEach((step, i) => {
            step.setAttribute('data-aos', 'fade-up');
            step.setAttribute('data-aos-duration', '500');
        });

        // Input focus effects with CSS transitions
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.style.transition = 'transform 0.2s ease-out';
            
            input.addEventListener('focus', () => {
                input.style.transform = 'scale(1.02)';
            });

            input.addEventListener('blur', () => {
                input.style.transform = 'scale(1)';
            });
        });

        // Button hover effects with CSS transitions
        const buttons = document.querySelectorAll('button:not(.aos-ignore)');
        buttons.forEach(button => {
            button.style.transition = 'transform 0.3s ease-out';
            
            button.addEventListener('mouseenter', () => {
                button.style.transform = 'scale(1.05)';
            });

            button.addEventListener('mouseleave', () => {
                button.style.transform = 'scale(1)';
            });
        });

        if (typeof AOS !== 'undefined') {
            AOS.refresh();
        }
    }

    // Search Results Animations
    function initSearchAnimations() {
        const resultsContainer = document.querySelector('#results-container');
        if (!resultsContainer) return;
        
        // Add AOS to donor cards
        const donorCards = document.querySelectorAll('#results-container > div');
        donorCards.forEach((card, i) => {
            card.setAttribute('data-aos', 'fade-up');
            card.setAttribute('data-aos-delay', (i * 100).toString());
            card.setAttribute('data-aos-duration', '600');
        });

        if (typeof AOS !== 'undefined') {
            AOS.refresh();
        }
    }

    // Navbar Animation
    function initNavbarAnimation() {
        const navbar = document.querySelector('.navbar');
        if (!navbar) return;

        // Navbar scroll effect with CSS transition
        navbar.style.transition = 'background-color 0.3s ease-out, backdrop-filter 0.3s ease-out';
        
        window.addEventListener('scroll', () => {
            const currentScrollY = window.scrollY;
            
            if (currentScrollY > 50) {
                navbar.style.backgroundColor = 'rgba(15, 23, 42, 0.95)';
                navbar.style.backdropFilter = 'blur(10px)';
            } else {
                navbar.style.backgroundColor = 'transparent';
                navbar.style.backdropFilter = 'none';
            }
        });
    }

    // Page Load Entrance Animations
    function initPageLoadAnimations() {
        // Add AOS to all elements with animate-on-scroll class
        const animatedElements = document.querySelectorAll('.animate-on-scroll');
        
        animatedElements.forEach((element, i) => {
            element.setAttribute('data-aos', 'fade-up');
            element.setAttribute('data-aos-delay', (i * 50).toString());
        });

        if (typeof AOS !== 'undefined') {
            AOS.refresh();
        }
    }

    // Initialize all animations
    function initAllAnimations() {
        initHeroAnimations();
        initStoryAnimations();
        initImpactAnimations();
        initFormAnimations();
        initNavbarAnimation();
        initPageLoadAnimations();
        
        // Listen for dynamic content
        document.addEventListener('searchResultsLoaded', initSearchAnimations);
    }

    // Run initialization
    initAllAnimations();

    // Export functions for external use
    window.BloodLifeAnimations = {
        initSearchAnimations,
        animateCounter
    };
});

// Utility functions for other scripts
window.animateDonorCardEntrance = function(cardElement) {
    cardElement.style.opacity = '0';
    cardElement.style.transform = 'translateY(30px) scale(0.95)';
    cardElement.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
    
    requestAnimationFrame(() => {
        cardElement.style.opacity = '1';
        cardElement.style.transform = 'translateY(0) scale(1)';
    });
};