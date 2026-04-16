// Enhanced home page animations and functionality with AOS
(function () {
  // Home page search functionality
  document.addEventListener('DOMContentLoaded', function() {
    const homeSearchForm = document.getElementById('home-search-form');
    const searchTypeSelect = document.getElementById('home-search-type');
    const bloodGroupSelect = document.getElementById('home-blood-group');
    const userQueryInput = document.getElementById('home-user-query');
    const pincodeInput = document.getElementById('home-pincode');
    const searchTypeError = document.getElementById('search-type-error');
    const bloodGroupError = document.getElementById('blood-group-error');
    const userQueryError = document.getElementById('user-query-error');
    const pincodeError = document.getElementById('pincode-error');
    const searchButtonText = document.getElementById('search-button-text');
    
    if (homeSearchForm) {
      // Handle search type selection
      if (searchTypeSelect) {
        searchTypeSelect.addEventListener('change', function() {
          const searchType = this.value;
          if (searchTypeError) searchTypeError.classList.add('hidden');

          // Reset all fields
          if (bloodGroupSelect) bloodGroupSelect.classList.add('hidden');
          if (userQueryInput) userQueryInput.classList.add('hidden');
          if (bloodGroupError) bloodGroupError.classList.add('hidden');
          if (userQueryError) userQueryError.classList.add('hidden');

          // Show appropriate fields based on search type
          if (searchType === 'donor') {
            if (bloodGroupSelect) bloodGroupSelect.classList.remove('hidden');
            if (searchButtonText) searchButtonText.textContent = 'Find Donors';
          } else if (searchType === 'user') {
            if (userQueryInput) userQueryInput.classList.remove('hidden');
            if (searchButtonText) searchButtonText.textContent = 'Search Users';
          } else if (searchType === 'request') {
            if (searchButtonText) searchButtonText.textContent = 'Create Request';
          }
        });
      }
      
      homeSearchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        let isValid = true;

        // Reset errors
        if (searchTypeError) searchTypeError.classList.add('hidden');
        if (bloodGroupError) bloodGroupError.classList.add('hidden');
        if (userQueryError) userQueryError.classList.add('hidden');
        if (pincodeError) pincodeError.classList.add('hidden');

        const searchType = searchTypeSelect ? searchTypeSelect.value : '';
        const bloodGroup = bloodGroupSelect ? bloodGroupSelect.value : '';
        const userQuery = userQueryInput ? userQueryInput.value : '';
        const pincode = pincodeInput ? pincodeInput.value : '';

        // Validate search type
        if (!searchType) {
          if (searchTypeError) searchTypeError.classList.remove('hidden');
          isValid = false;
        }

        // Validate based on search type
        if (searchType === 'donor' && !bloodGroup) {
          if (bloodGroupError) bloodGroupError.classList.remove('hidden');
          isValid = false;
        }

        if (searchType === 'user' && !userQuery.trim()) {
          if (userQueryError) userQueryError.classList.remove('hidden');
          isValid = false;
        }

        // Validate pincode if entered
        if (pincode && !/^[0-9]{6}$/.test(pincode)) {
          if (pincodeError) pincodeError.classList.remove('hidden');
          isValid = false;
        }
        
        if (!isValid) {
          return;
        }
        
        // Show loading state
        const submitButton = homeSearchForm.querySelector('button[type="submit"]');
        if (submitButton) {
          const originalText = submitButton.innerHTML;
          submitButton.innerHTML = '<svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></svg> Processing...';
          submitButton.disabled = true;
        }
        
        // Handle different search types
        let url = '';
        if (searchType === 'donor') {
          url = '/search/donors/?blood_group=' + encodeURIComponent(bloodGroup);
          if (pincode) {
            url += '&pincode=' + encodeURIComponent(pincode);
          }
        } else if (searchType === 'user') {
          url = '/search/users/?query=' + encodeURIComponent(userQuery);
          if (pincode) {
            url += '&pincode=' + encodeURIComponent(pincode);
          }
        } else if (searchType === 'request') {
          url = '/requests/create/';
        }
        
        // Add slight delay to show loading state
        setTimeout(() => {
          window.location.href = url;
        }, 500);
      });

      // Add real-time validation for pincode
      if (pincodeInput) {
        pincodeInput.addEventListener('input', function() {
          const value = this.value;
          if (value && !/^[0-9]{6}$/.test(value)) {
            pincodeError.classList.remove('hidden');
          } else {
            pincodeError.classList.add('hidden');
          }
        });

        // Remove error when user starts typing
        pincodeInput.addEventListener('focus', function() {
          pincodeError.classList.add('hidden');
        });
      }

      // Remove error when blood group is selected
      if (bloodGroupSelect) {
        bloodGroupSelect.addEventListener('change', function() {
          bloodGroupError.classList.add('hidden');
        });
      }
      
      // Remove error when user starts typing in user query
      if (userQueryInput) {
        userQueryInput.addEventListener('input', function() {
          userQueryError.classList.add('hidden');
        });
        
        userQueryInput.addEventListener('focus', function() {
          userQueryError.classList.add('hidden');
        });
      }

      // Remove error when search type is selected
      if (searchTypeSelect) {
        searchTypeSelect.addEventListener('change', function() {
          searchTypeError.classList.add('hidden');
        });
      }
    }

    // Initialize periodic card animations for "every 2 seconds" section
    initPeriodicCardAnimations();

    // Initialize enhanced scroll animations after a brief delay to avoid conflicts
    setTimeout(initEnhancedScrollAnimations, 200);
  });

  // Enhanced scroll animations for sections and images - using AOS
  function initEnhancedScrollAnimations() {
    // Use AOS for scroll animations
    if (typeof AOS !== 'undefined') {
      // Add AOS to elements that need scroll animations
      const animateElements = document.querySelectorAll('.animate-on-scroll:not([data-aos])');
      
      animateElements.forEach((element, index) => {
        element.setAttribute('data-aos', 'fade-up');
        element.setAttribute('data-aos-delay', (index * 100).toString());
      });
      
      AOS.refresh();
    } else {
      // Fallback to simple scroll animations if AOS is not available
      function onScroll() {
        const fadeElems = document.querySelectorAll(".scroll-fade");
        const parallaxElems = document.querySelectorAll(".scroll-parallax");
        const viewportHeight = window.innerHeight || document.documentElement.clientHeight;

        fadeElems.forEach((el) => {
          const rect = el.getBoundingClientRect();
          if (rect.top < viewportHeight * 0.85) {
            el.classList.add("visible");
          }
        });

        const scrollY = window.scrollY || window.pageYOffset;
        parallaxElems.forEach((el) => {
          const speed = 0.12;
          const offset = (scrollY - el.offsetTop) * speed;
          el.style.transform = `translateY(${offset}px)`;
        });
      }

      window.addEventListener("scroll", onScroll, { passive: true });
      window.addEventListener("load", onScroll);
      setTimeout(onScroll, 50);
    }
  }

  // Initialize periodic animations for cards that appear every 2 seconds
  function initPeriodicCardAnimations() {
    // Check if we have the "every 2 seconds" card elements to animate
    const statCard = document.querySelector('.hero-media-card');
    if (statCard) {
      // Add CSS animation for pulsating effect
      statCard.style.animation = 'pulse 2s ease-in-out infinite';
      
      // Add CSS animation for floating effect
      statCard.style.animation = 'float 3s ease-in-out infinite';
    }

    // Add animations to other cards that should cycle periodically
    animateNeedsBloodCards();
  }

  // Animate "needs blood" cards periodically
  function animateNeedsBloodCards() {
    // Find elements that need periodic animation
    const needsBloodElements = document.querySelectorAll('.story-point.periodic-highlight, .impact-card.periodic-highlight, .steps > li.periodic-highlight');
    if (needsBloodElements.length > 0) {
      // Add subtle periodic animation to highlight these cards
      needsBloodElements.forEach((element, index) => {
        // Add CSS animation for glow effect
        element.style.animation = `glow 4s ease-in-out ${index}s infinite`;
        
        // Add CSS animation for background pulse
        element.style.animation = `pulse-bg 1.5s ease-in-out ${index * 0.2}s infinite`;
      });
    }
  }

  // Enhanced AOS animations with element existence checks
  if (typeof AOS !== 'undefined') {
    // Ensure DOM is ready before running animations
    setTimeout(() => {
      // Hero section entrance animation - only if elements exist
      const heroTitle = document.querySelector('.hero h1');
      if (heroTitle && !heroTitle.classList.contains('animated') && !heroTitle.classList.contains('home-animated')) {
        heroTitle.setAttribute('data-aos', 'fade-up');
        heroTitle.setAttribute('data-aos-delay', '200');
        heroTitle.classList.add('home-animated');
      }
      
      const heroCopy = document.querySelector('.hero-copy');
      if (heroCopy && !heroCopy.classList.contains('animated') && !heroCopy.classList.contains('home-animated')) {
        heroCopy.setAttribute('data-aos', 'fade-up');
        heroCopy.setAttribute('data-aos-delay', '400');
        heroCopy.classList.add('home-animated');
      }
      
      // Staggered button animations - only if elements exist
      const heroButtons = document.querySelectorAll('.hero-actions a');
      heroButtons.forEach((btn, index) => {
        btn.setAttribute('data-aos', 'fade-up');
        btn.setAttribute('data-aos-delay', (600 + index * 100).toString());
        btn.classList.add('home-animated');
      });
      
      // Animated counter for impact section - only if elements exist
      const counters = document.querySelectorAll('.impact-number');
      counters.forEach(counter => {
        if (counter && !counter.dataset.animated) {
          const target = parseInt(counter.getAttribute('data-count-to'));
          if (target) {
            counter.setAttribute('data-aos', 'fade-up');
            counter.setAttribute('data-aos-once', 'true');
            
            counter.addEventListener('aos:in', () => {
              const duration = 2;
              const increment = target / (duration * 60);
              let current = 0;
              
              const updateCounter = () => {
                current += increment;
                if (current < target) {
                  counter.textContent = Math.floor(current);
                  requestAnimationFrame(updateCounter);
                } else {
                  counter.textContent = target;
                }
              };
              
              updateCounter();
              counter.dataset.animated = 'true';
            });
          }
        }
      });

      // Add periodic animations to hero background elements
      animateHeroBackground();
      
      // Refresh AOS after adding attributes
      AOS.refresh();
    }, 150); // Small delay to ensure DOM is ready
  }

  // Animate hero background elements continuously with CSS
  function animateHeroBackground() {
    const bgElement1 = document.querySelector('.hero .absolute:nth-child(2) .absolute:nth-child(1)');
    if (bgElement1) {
      bgElement1.style.animation = 'float-bg 8s ease-in-out infinite';
    }

    const bgElement2 = document.querySelector('.hero .absolute:nth-child(2) .absolute:nth-child(2)');
    if (bgElement2) {
      bgElement2.style.animation = 'float-bg 10s ease-in-out infinite';
    }
    
    // Add pulse animation to the hero background circles
    const heroCircles = document.querySelectorAll('.hero .absolute div.bg-red-500\\/10, .hero .absolute div.bg-blue-500\\/10');
    heroCircles.forEach((circle, index) => {
      circle.style.animation = `pulse-circle 2.5s ease-in-out ${index * 0.5}s infinite`;
    });
  }

  // 3D Card Tilt Effect on Hover with CSS
  function initCardTiltEffect() {
    const cards = document.querySelectorAll('.glass-card');
    cards.forEach(card => {
      card.style.transition = 'transform 0.3s ease-out';
      
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 20;
        const rotateY = (centerX - x) / 20;
        
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
      });
      
      card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0)';
      });
    });
  }

  // Magnetic Button Effect with CSS
  function initMagneticButtons() {
    const buttons = document.querySelectorAll('.btn-animated, button[type="submit"]');
    buttons.forEach(button => {
      button.style.transition = 'transform 0.3s ease-out';
      
      button.addEventListener('mousemove', (e) => {
        const rect = button.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        
        button.style.transform = `translate(${x * 0.2}px, ${y * 0.2}px)`;
      });
      
      button.addEventListener('mouseleave', () => {
        button.style.transform = 'translate(0, 0)';
      });
      
      // Button press effect
      button.addEventListener('mousedown', () => {
        button.style.transform = 'scale(0.95)';
      });
      
      button.addEventListener('mouseup', () => {
        button.style.transform = 'scale(1)';
      });
    });
  }

  // Input Field Focus Glow Effect with CSS
  function initInputFocusEffects() {
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
      input.style.transition = 'box-shadow 0.3s ease-out, border-color 0.3s ease-out';
      
      input.addEventListener('focus', () => {
        input.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.3)';
        input.style.borderColor = 'rgba(239, 68, 68, 0.6)';
      });
      
      input.addEventListener('blur', () => {
        input.style.boxShadow = '0 0 0 0px rgba(239, 68, 68, 0)';
        input.style.borderColor = 'rgba(255, 255, 255, 0.2)';
      });
    });
  }

  // Initialize all enhanced animations
  setTimeout(() => {
    initCardTiltEffect();
    initMagneticButtons();
    initInputFocusEffects();
  }, 500);
})();


