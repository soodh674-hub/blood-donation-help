// Enhanced home page animations and functionality
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
      searchTypeSelect.addEventListener('change', function() {
        const searchType = this.value;
        searchTypeError.classList.add('hidden');
        
        // Reset all fields
        bloodGroupSelect.classList.add('hidden');
        userQueryInput.classList.add('hidden');
        bloodGroupError.classList.add('hidden');
        userQueryError.classList.add('hidden');
        
        // Show appropriate fields based on search type
        if (searchType === 'donor') {
          bloodGroupSelect.classList.remove('hidden');
          searchButtonText.textContent = 'Find Donors';
        } else if (searchType === 'user') {
          userQueryInput.classList.remove('hidden');
          searchButtonText.textContent = 'Search Users';
        } else if (searchType === 'request') {
          searchButtonText.textContent = 'Create Request';
        }
      });
      
      homeSearchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        let isValid = true;
        
        // Reset errors
        searchTypeError.classList.add('hidden');
        bloodGroupError.classList.add('hidden');
        userQueryError.classList.add('hidden');
        pincodeError.classList.add('hidden');
        
        const searchType = searchTypeSelect.value;
        const bloodGroup = bloodGroupSelect.value;
        const userQuery = userQueryInput.value;
        const pincode = pincodeInput.value;
        
        // Validate search type
        if (!searchType) {
          searchTypeError.classList.remove('hidden');
          isValid = false;
        }
        
        // Validate based on search type
        if (searchType === 'donor' && !bloodGroup) {
          bloodGroupError.classList.remove('hidden');
          isValid = false;
        }
        
        if (searchType === 'user' && !userQuery.trim()) {
          userQueryError.classList.remove('hidden');
          isValid = false;
        }
        
        // Validate pincode if entered
        if (pincode && !/^[0-9]{6}$/.test(pincode)) {
          pincodeError.classList.remove('hidden');
          isValid = false;
        }
        
        if (!isValid) {
          return;
        }
        
        // Show loading state
        const submitButton = homeSearchForm.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></svg> Processing...';
        submitButton.disabled = true;
        
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

  // Enhanced scroll animations for sections and images - only for elements not handled by base template
  function initEnhancedScrollAnimations() {
    // Check if GSAP is available
    if (typeof gsap === 'undefined') {
      // Fallback to simple scroll animations if GSAP is not available
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
      setTimeout(onScroll, 50); // Small delay to catch elements already in view
      return;
    }

    // Use GSAP for enhanced animations if available
    gsap.registerPlugin(ScrollTrigger);

    // Enhanced scroll-triggered animations for home page specific elements
    const animateElements = document.querySelectorAll('.animate-on-scroll:not(.home-animated)');
    
    animateElements.forEach((element, index) => {
      // Check if element is already animated by other scripts
      if (!element.classList.contains('animated')) {
        // Add delay based on element's existing animation-delay property
        const delay = parseFloat(element.style.animationDelay || 0);
        
        gsap.fromTo(element,
          { opacity: 0, y: 30 },
          {
            opacity: 1,
            y: 0,
            duration: 0.8,
            delay: delay,
            scrollTrigger: {
              trigger: element,
              start: "top 85%",
              toggleActions: "play none none reverse"
            },
            onComplete: function() {
              element.classList.add('home-animated'); // Mark as animated by this script
            }
          }
        );
      }
    });
  }

  // Initialize periodic animations for cards that appear every 2 seconds
  function initPeriodicCardAnimations() {
    // Check if we have the "every 2 seconds" card elements to animate
    const statCard = document.querySelector('.hero-media-card');
    if (statCard) {
      // Create a pulsating effect for the "every 2 seconds" message
      let isVisible = true;
      setInterval(() => {
        if (isVisible) {
          gsap.to(statCard, {
            opacity: 0.7,
            scale: 0.98,
            duration: 0.8,
            ease: "power2.inOut"
          });
        } else {
          gsap.to(statCard, {
            opacity: 1,
            scale: 1,
            duration: 0.8,
            ease: "power2.inOut"
          });
        }
        isVisible = !isVisible;
      }, 2000); // Every 2 seconds

      // Add floating animation to the card
      gsap.to(statCard, {
        y: -15,
        duration: 3,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: 0.5
      });
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
        // Add a subtle glow effect every 2 seconds
        setInterval(() => {
          gsap.fromTo(element, 
            { 
              boxShadow: "0 0 0 0 rgba(239, 68, 68, 0.4)",
              borderColor: "rgba(239, 68, 68, 0.3)"
            },
            { 
              boxShadow: "0 0 0 10px rgba(239, 68, 68, 0)",
              borderColor: "rgba(239, 68, 68, 0.5)",
              duration: 2,
              ease: "power2.out"
            }
          );
        }, 4000 + (index * 1000)); // Stagger the animations
        
        // Also add a subtle pulse effect to the background
        gsap.to(element, {
          backgroundColor: "rgba(255, 255, 255, 0.08)",
          duration: 1.5,
          repeat: -1,
          yoyo: true,
          ease: "sine.inOut",
          delay: index * 0.2
        });
      });
    }
  }

  // Enhanced GSAP animations with element existence checks
  if (typeof gsap !== 'undefined') {
    // Ensure DOM is ready before running animations
    setTimeout(() => {
      // Hero section entrance animation - only if elements exist
      const heroTitle = document.querySelector('.hero h1');
      if (heroTitle && !heroTitle.classList.contains('animated') && !heroTitle.classList.contains('home-animated')) {
        gsap.from(heroTitle, {
          opacity: 0,
          y: 50,
          duration: 1,
          delay: 0.2,
          ease: 'power3.out',
          onComplete: function() {
            heroTitle.classList.add('home-animated');
          }
        });
      }
      
      const heroCopy = document.querySelector('.hero-copy');
      if (heroCopy && !heroCopy.classList.contains('animated') && !heroCopy.classList.contains('home-animated')) {
        gsap.from(heroCopy, {
          opacity: 0,
          y: 30,
          duration: 1,
          delay: 0.4,
          ease: 'power2.out',
          onComplete: function() {
            heroCopy.classList.add('home-animated');
          }
        });
      }
      
      // Staggered button animations - only if elements exist
      const heroButtons = gsap.utils.toArray('.hero-actions a');
      if (heroButtons.length > 0) {
        gsap.from(heroButtons, {
          opacity: 0,
          y: 20,
          duration: 0.8,
          delay: 0.6,
          stagger: 0.1,
          ease: 'back.out(1.7)',
          onComplete: function() {
            heroButtons.forEach(btn => {
              btn.classList.add('home-animated');
            });
          }
        });
      }
      
      // Animated counter for impact section - only if elements exist
      const counters = document.querySelectorAll('.impact-number');
      counters.forEach(counter => {
        if (counter && !counter.dataset.animated) {
          const target = parseInt(counter.getAttribute('data-count-to'));
          if (target) {
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
            
            // Start counter when element comes into view
            const observer = new IntersectionObserver((entries) => {
              entries.forEach(entry => {
                if (entry.isIntersecting) {
                  updateCounter();
                  counter.dataset.animated = 'true'; // Mark as animated
                  observer.unobserve(entry.target);
                }
              });
            });
            
            observer.observe(counter);
          }
        }
      });

      // Add periodic animations to hero background elements
      animateHeroBackground();
    }, 150); // Small delay to ensure DOM is ready
  }

  // Animate hero background elements continuously
  function animateHeroBackground() {
    const bgElement1 = document.querySelector('.hero .absolute:nth-child(2) .absolute:nth-child(1)');
    if (bgElement1) {
      gsap.to(bgElement1, {
        x: -50,
        y: -30,
        scale: 1.05,
        duration: 8,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut"
      });
    }

    const bgElement2 = document.querySelector('.hero .absolute:nth-child(2) .absolute:nth-child(2)');
    if (bgElement2) {
      gsap.to(bgElement2, {
        x: 30,
        y: 40,
        scale: 1.1,
        duration: 10,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut"
      });
    }
    
    // Add pulse animation to the hero background circles
    const heroCircles = document.querySelectorAll('.hero .absolute div.bg-red-500\\/10, .hero .absolute div.bg-blue-500\\/10');
    heroCircles.forEach((circle, index) => {
      gsap.to(circle, {
        scale: 1.1,
        opacity: 0.7,
        duration: 2.5,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: index * 0.5
      });
    });
  }

  // 3D Card Tilt Effect on Hover
  function initCardTiltEffect() {
    if (typeof gsap === 'undefined') return;
    
    gsap.utils.toArray('.glass-card').forEach(card => {
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 20;
        const rotateY = (centerX - x) / 20;
        
        gsap.to(card, {
          rotationX: rotateX,
          rotationY: rotateY,
          transformPerspective: 1000,
          duration: 0.3,
          ease: 'power2.out'
        });
      });
      
      card.addEventListener('mouseleave', () => {
        gsap.to(card, {
          rotationX: 0,
          rotationY: 0,
          duration: 0.5,
          ease: 'elastic.out(1, 0.5)'
        });
      });
    });
  }

  // Magnetic Button Effect
  function initMagneticButtons() {
    if (typeof gsap === 'undefined') return;
    
    gsap.utils.toArray('.btn-animated, button[type="submit"]').forEach(button => {
      button.addEventListener('mousemove', (e) => {
        const rect = button.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        
        gsap.to(button, {
          x: x * 0.2,
          y: y * 0.2,
          duration: 0.3,
          ease: 'power2.out'
        });
      });
      
      button.addEventListener('mouseleave', () => {
        gsap.to(button, {
          x: 0,
          y: 0,
          duration: 0.5,
          ease: 'elastic.out(1, 0.3)'
        });
      });
      
      // Button press effect
      button.addEventListener('mousedown', () => {
        gsap.to(button, {
          scale: 0.95,
          duration: 0.1
        });
      });
      
      button.addEventListener('mouseup', () => {
        gsap.to(button, {
          scale: 1,
          duration: 0.3,
          ease: 'elastic.out(1, 0.5)'
        });
      });
    });
  }

  // Input Field Focus Glow Effect
  function initInputFocusEffects() {
    if (typeof gsap === 'undefined') return;
    
    gsap.utils.toArray('input, select, textarea').forEach(input => {
      input.addEventListener('focus', () => {
        gsap.to(input, {
          boxShadow: '0 0 0 3px rgba(239, 68, 68, 0.3)',
          borderColor: 'rgba(239, 68, 68, 0.6)',
          duration: 0.3,
          ease: 'power2.out'
        });
      });
      
      input.addEventListener('blur', () => {
        gsap.to(input, {
          boxShadow: '0 0 0 0px rgba(239, 68, 68, 0)',
          borderColor: 'rgba(255, 255, 255, 0.2)',
          duration: 0.3,
          ease: 'power2.out'
        });
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


