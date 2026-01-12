/**
 * MicroBlogHub - Enhanced JavaScript
 * Modern, feature-rich interactions for the MicroBlogHub application
 */

(function() {
    'use strict';

    // ============================================
    // Configuration & Constants
    // ============================================
    const CONFIG = {
        MAX_POST_LENGTH: 280,
        WARNING_THRESHOLD: 250,
        CAUTION_THRESHOLD: 200,
        ANIMATION_DURATION: 300,
        DEBOUNCE_DELAY: 300
    };

    // ============================================
    // Utility Functions
    // ============================================
    
    /**
     * Debounce function to limit function calls
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Smooth scroll to element
     */
    function smoothScrollTo(element, offset = 0) {
        if (!element) return;
        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - offset;
        
        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }

    /**
     * Add fade-in animation to elements
     */
    function fadeIn(element, duration = CONFIG.ANIMATION_DURATION) {
        if (!element) return;
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = null;
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = Math.min(progress / duration, 1);
            element.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        }
        requestAnimationFrame(animate);
    }

    /**
     * Add fade-out animation to elements
     */
    function fadeOut(element, duration = CONFIG.ANIMATION_DURATION) {
        if (!element) return;
        let start = null;
        const initialOpacity = parseFloat(window.getComputedStyle(element).opacity);
        
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = Math.max(initialOpacity - (progress / duration), 0);
            element.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
            }
        }
        requestAnimationFrame(animate);
    }

    /**
     * Show toast notification
     */
    function showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--bg-elevated);
            color: var(--text);
            padding: 1rem 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            animation: slideInRight 0.3s ease-out;
            max-width: 300px;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            fadeOut(toast, 300);
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    // ============================================
    // Character Counter Module (Disabled - No Limit)
    // ============================================
    const CharacterCounter = {
        init() {
            // Character counter disabled - no limit on posts
            // This module is kept for potential future use
        }
    };

    // ============================================
    // Comments Module
    // ============================================
    const CommentsModule = {
        init() {
            // Make toggleComments available globally (for old structure compatibility)
            window.toggleComments = this.toggleComments.bind(this);
            window.toggleCommentsList = this.toggleCommentsList.bind(this);
            
            const commentButtons = document.querySelectorAll('.comment-btn');
            
            commentButtons.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.toggleComments(btn);
                });
            });

            // Initialize comments list toggles
            const commentsViewToggles = document.querySelectorAll('.comments-view-toggle');
            commentsViewToggles.forEach(toggle => {
                toggle.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.toggleCommentsList(toggle);
                });
            });

            // Auto-expand comments list when form is submitted successfully
            const commentForms = document.querySelectorAll('.comment-form');
            commentForms.forEach(form => {
                form.addEventListener('submit', () => {
                    // After form submission, show the comments list
                    const post = form.closest('.post');
                    if (post) {
                        const commentsList = post.querySelector('.comments-list-container');
                        const toggleBtn = post.querySelector('.comments-view-toggle');
                        if (commentsList && toggleBtn && (commentsList.style.display === 'none' || window.getComputedStyle(commentsList).display === 'none')) {
                            setTimeout(() => {
                                this.toggleCommentsList(toggleBtn);
                            }, 500); // Wait for page reload/redirect
                        }
                    }
                });
            });
        },

        toggleComments(button) {
            // Legacy function for old comment structure
            const post = button.closest('.post');
            if (!post) return;

            const commentsSection = post.querySelector('.comments');
            if (!commentsSection) return;

            const isHidden = commentsSection.style.display === 'none' || 
                            window.getComputedStyle(commentsSection).display === 'none';

            if (isHidden) {
                commentsSection.style.display = 'block';
                fadeIn(commentsSection, CONFIG.ANIMATION_DURATION);
                smoothScrollTo(commentsSection, 100);
                
                // Focus on comment input if available
                const commentInput = commentsSection.querySelector('input[type="text"]');
                if (commentInput) {
                    setTimeout(() => commentInput.focus(), CONFIG.ANIMATION_DURATION);
                }
            } else {
                fadeOut(commentsSection, CONFIG.ANIMATION_DURATION);
            }

            // Update button state
            button.classList.toggle('active');
        },

        toggleCommentsList(button) {
            const postId = button.dataset.postId;
            const commentsList = document.getElementById(`comments-${postId}`);
            if (!commentsList) return;

            const isHidden = commentsList.style.display === 'none' || 
                            window.getComputedStyle(commentsList).display === 'none';

            const arrow = button.querySelector('.toggle-arrow');

            if (isHidden) {
                commentsList.style.display = 'block';
                fadeIn(commentsList, CONFIG.ANIMATION_DURATION);
                if (arrow) arrow.textContent = '▲';
                button.classList.add('active');
            } else {
                fadeOut(commentsList, CONFIG.ANIMATION_DURATION);
                if (arrow) arrow.textContent = '▼';
                button.classList.remove('active');
            }
        }
    };

    // Make functions globally available
    window.toggleAllComments = function(button) {
        const postId = button.dataset.postId;
        const commentsList = document.getElementById(`comments-${postId}`);
        if (!commentsList) return;

        const hiddenComments = commentsList.querySelectorAll('.comment-hidden');
        const showMoreBtn = document.getElementById(`show-more-${postId}`);
        const arrow = button.querySelector('.toggle-arrow');

        if (hiddenComments.length > 0) {
            // Show all hidden comments
            hiddenComments.forEach(comment => {
                comment.style.display = 'flex';
                comment.classList.remove('comment-hidden');
                fadeIn(comment, 200);
            });

            // Hide "show more" button
            if (showMoreBtn) {
                showMoreBtn.style.display = 'none';
            }

            // Update toggle button
            button.querySelector('.toggle-text').textContent = 'Show Less';
            if (arrow) arrow.textContent = '▲';
            button.classList.add('active');
        } else {
            // Hide comments beyond first 3
            const allComments = commentsList.querySelectorAll('.comment-item');
            allComments.forEach((comment, index) => {
                if (index >= 3) {
                    comment.style.display = 'none';
                    comment.classList.add('comment-hidden');
                }
            });

            // Show "show more" button
            if (showMoreBtn) {
                showMoreBtn.style.display = 'block';
            }

            // Update toggle button
            button.querySelector('.toggle-text').textContent = 'Show All';
            if (arrow) arrow.textContent = '▼';
            button.classList.remove('active');

            // Scroll to top of comments
            smoothScrollTo(commentsList, 100);
        }
    };

    window.showMoreComments = function(postId) {
        const commentsList = document.getElementById(`comments-${postId}`);
        if (!commentsList) return;

        const hiddenComments = commentsList.querySelectorAll('.comment-hidden');
        const showMoreBtn = document.getElementById(`show-more-${postId}`);

        if (hiddenComments.length > 0) {
            // Show next 3 comments (or remaining)
            const toShow = Math.min(3, hiddenComments.length);
            for (let i = 0; i < toShow; i++) {
                hiddenComments[i].style.display = 'flex';
                hiddenComments[i].classList.remove('comment-hidden');
                fadeIn(hiddenComments[i], 200);
            }

            // Update button text or hide if all shown
            const remaining = hiddenComments.length - toShow;
            if (remaining <= 0 && showMoreBtn) {
                showMoreBtn.style.display = 'none';
            } else if (showMoreBtn) {
                const btn = showMoreBtn.querySelector('.show-more-comments-btn');
                if (btn) {
                    const textSpan = btn.querySelector('.show-more-text');
                    if (textSpan) {
                        textSpan.textContent = 
                            `Show ${remaining} more comment${remaining !== 1 ? 's' : ''}`;
                    }
                }
            }
        }
    };

    // Initialize show more buttons
    function initShowMoreButtons() {
        const showMoreButtons = document.querySelectorAll('.show-more-comments-btn');
        showMoreButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const postId = this.dataset.postId;
                if (postId) {
                    showMoreComments(parseInt(postId, 10));
                }
            });
        });
    }

    // Like/Unlike Button Enhancements
    function initLikeButtons() {
        const likeButtons = document.querySelectorAll('.like-btn, .liked-btn');
        
        likeButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                // Add visual feedback
                const icon = this.querySelector('.action-icon');
                if (icon) {
                    icon.style.animation = 'none';
                    setTimeout(() => {
                        icon.style.animation = 'heartBeat 0.6s ease';
                    }, 10);
                }
                
                // Add ripple effect
                const ripple = document.createElement('span');
                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.cssText = `
                    position: absolute;
                    width: ${size}px;
                    height: ${size}px;
                    border-radius: 50%;
                    background: rgba(239, 68, 68, 0.3);
                    left: ${x}px;
                    top: ${y}px;
                    pointer-events: none;
                    animation: ripple 0.6s ease-out;
                `;
                
                if (getComputedStyle(this).position === 'static') {
                    this.style.position = 'relative';
                }
                this.style.overflow = 'hidden';
                this.appendChild(ripple);
                
                setTimeout(() => ripple.remove(), 600);
            });
        });
    }

    // ============================================
    // Form Enhancements Module
    // ============================================
    const FormEnhancements = {
        init() {
            const forms = document.querySelectorAll('form');
            
            forms.forEach(form => {
                // Add loading state to submit buttons
                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn && !form.dataset.preventLoading) {
                    submitBtn.addEventListener('click', (e) => {
                        this.setLoadingState(submitBtn, true);
                    });
                }

                // Add validation feedback
                const inputs = form.querySelectorAll('input, textarea');
                inputs.forEach(input => {
                    input.addEventListener('blur', () => {
                        this.validateInput(input);
                    });

                    input.addEventListener('input', debounce(() => {
                        if (input.value) {
                            this.validateInput(input);
                        }
                    }, CONFIG.DEBOUNCE_DELAY));
                });
            });
        },

        setLoadingState(button, isLoading) {
            if (isLoading) {
                button.dataset.originalText = button.textContent || button.value;
                button.textContent = button.textContent ? 'Loading...' : '';
                button.value = button.value ? 'Loading...' : '';
                button.style.opacity = '0.7';
                button.style.cursor = 'wait';
            } else {
                button.textContent = button.dataset.originalText || button.textContent;
                button.value = button.dataset.originalText || button.value;
                button.style.opacity = '1';
                button.style.cursor = 'pointer';
                delete button.dataset.originalText;
            }
        },

        validateInput(input) {
            // Remove previous validation classes
            input.classList.remove('valid', 'invalid');

            if (!input.value.trim()) {
                return;
            }

            // Basic validation
            if (input.validity.valid) {
                input.classList.add('valid');
            } else {
                input.classList.add('invalid');
            }
        }
    };

    // ============================================
    // Interactive Elements Module
    // ============================================
    const InteractiveElements = {
        init() {
            // Add ripple effect to buttons
            const buttons = document.querySelectorAll('button, .btn-follow, .primary-btn, .auth-submit-btn, .comment-submit-btn');
            buttons.forEach(btn => {
                btn.addEventListener('click', this.createRipple);
            });

            // Add hover effects to cards
            const cards = document.querySelectorAll('.post, .profile-post-card, .composer-card');
            cards.forEach(card => {
                card.addEventListener('mouseenter', () => {
                    card.style.transform = 'translateY(-2px)';
                });
                card.addEventListener('mouseleave', () => {
                    card.style.transform = 'translateY(0)';
                });
            });

            // Keyboard navigation for accessibility
            this.initKeyboardNavigation();
        },

        createRipple(e) {
            const button = e.currentTarget;
            const ripple = document.createElement('span');
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.3);
                left: ${x}px;
                top: ${y}px;
                pointer-events: none;
                animation: ripple 0.6s ease-out;
            `;

            if (getComputedStyle(button).position === 'static') {
                button.style.position = 'relative';
            }
            button.style.overflow = 'hidden';

            button.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        },

        initKeyboardNavigation() {
            document.addEventListener('keydown', (e) => {
                // Escape key to close modals/comments
                if (e.key === 'Escape') {
                    const openComments = document.querySelectorAll('.comments[style*="block"]');
                    openComments.forEach(comments => {
                        const toggleBtn = comments.closest('.post')?.querySelector('.comment-btn');
                        if (toggleBtn) {
                            CommentsModule.toggleComments(toggleBtn);
                        }
                    });
                }

                // Ctrl/Cmd + Enter to submit forms
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    const focusedInput = document.activeElement;
                    if (focusedInput && (focusedInput.tagName === 'TEXTAREA' || focusedInput.tagName === 'INPUT')) {
                        const form = focusedInput.closest('form');
                        if (form && !focusedInput.closest('.comment-form')) {
                            form.requestSubmit();
                        }
                    }
                }
            });
        }
    };

    // ============================================
    // Navigation Module
    // ============================================
    const NavigationModule = {
        init() {
            // Highlight active navigation links
            const currentPath = window.location.pathname;
            const navLinks = document.querySelectorAll('.nav-link');
            
            navLinks.forEach(link => {
                if (link.getAttribute('href') === currentPath) {
                    link.classList.add('active');
                }
            });

            // Smooth scroll for anchor links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', (e) => {
                    const href = anchor.getAttribute('href');
                    if (href !== '#') {
                        e.preventDefault();
                        const target = document.querySelector(href);
                        if (target) {
                            smoothScrollTo(target, 80);
                        }
                    }
                });
            });
        }
    };

    // ============================================
    // Search Highlight & Hashtag Linkify Module
    // ============================================
    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function highlightAndLinkifyInContainer(container, query) {
        if (!container) return;
        // Linkify hashtags first
        const hs = container.querySelectorAll('.post-body');
        hs.forEach(el => {
            let html = el.innerHTML;
            // linkify hashtags
            html = html.replace(/#(\w+)/g, '<a class="hashtag-chip" href="' + window.location.pathname + '?q=%23$1">#$1</a>');
            el.innerHTML = html;
        });

        if (!query) return;
        const words = query.split(/\s+/).filter(Boolean);
        if (words.length === 0) return;

        words.forEach(w => {
            const wEsc = escapeRegExp(w.replace(/^[@#]/, ''));
            if (!wEsc) return;
            const regex = new RegExp(`(${wEsc})`, 'gi');
            hs.forEach(el => {
                // avoid highlighting inside tags
                el.innerHTML = el.innerHTML.replace(regex, '<span class="mark-highlight">$1</span>');
            });
        });
    }

    function highlightSearchMatches() {
        const main = document.querySelector('[data-query]');
        if (!main) return;
        const query = (main.dataset.query || '').trim();
        highlightAndLinkifyInContainer(main, query);


    }

    // ============================================
    // Delete modal handlers (global)
    // ============================================

    function openDeleteModal(url, postContent) {
        const modal = document.getElementById('deleteModal');
        const form = document.getElementById('deleteForm');
        const text = document.getElementById('deleteModalText');
        if (!modal || !form || !text) return;
        form.action = url;
        text.textContent = postContent && postContent.length ? 'Delete the post: "' + postContent.slice(0,140) + (postContent.length>140 ? '…' : '') + '"?' : 'Are you sure you want to delete this post?';
        modal.style.display = 'flex';
        modal.setAttribute('aria-hidden', 'false');
        document.getElementById('cancelDeleteBtn')?.focus();
    }

    function closeDeleteModal() {
        const modal = document.getElementById('deleteModal');
        if (!modal) return;
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
    }

    function attachDeleteButtons() {
        document.querySelectorAll('.delete-btn').forEach(btn => {
            if (btn.dataset.deleteAttached) return;
            btn.addEventListener('click', (e)=>{
                const url = btn.dataset.deleteUrl;
                const content = btn.dataset.postContent || '';
                openDeleteModal(url, content);
            });
            btn.dataset.deleteAttached = '1';
        });
    }

    document.addEventListener('DOMContentLoaded', ()=>{
        attachDeleteButtons();

        const cancelBtn = document.getElementById('cancelDeleteBtn');
        if (cancelBtn) cancelBtn.addEventListener('click', (e)=>{ e.preventDefault(); closeDeleteModal(); });

        const modalOverlay = document.querySelector('#deleteModal .modal-overlay');
        if (modalOverlay) modalOverlay.addEventListener('click', closeDeleteModal);

        // close modal with Escape
        document.addEventListener('keydown', (e)=>{ if (e.key === 'Escape') closeDeleteModal(); });
    });

    // ============================================
    // Animation Styles Injection
    // ============================================
    function injectAnimationStyles() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }

            @keyframes pulse {
                0%, 100% {
                    transform: scale(1);
                }
                50% {
                    transform: scale(1.05);
                }
            }

            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            .comment-btn.active {
                background: var(--accent-soft);
                color: var(--accent);
            }

            input.valid {
                border-color: #22c55e !important;
            }

            input.invalid {
                border-color: #ef4444 !important;
            }
        `;
        document.head.appendChild(style);
    }

    // ============================================
    // Initialization
    // ============================================
    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeApp);
        } else {
            initializeApp();
        }
    }

    function initializeApp() {
        // Inject animation styles
        injectAnimationStyles();

        // Initialize all modules
        try {
            CharacterCounter.init();
            CommentsModule.init();
            FormEnhancements.init();
            InteractiveElements.init();
            NavigationModule.init();
            initShowMoreButtons();
            initLikeButtons();

            // Highlight matches and linkify hashtags on search results page
            try { highlightSearchMatches(); } catch (e) { /* non-critical */ }

            console.log('✨ MicroBlogHub enhanced JavaScript loaded successfully!');
        } catch (error) {
            console.error('❌ Error initializing MicroBlogHub JavaScript:', error);
        }
    }

    // ============================================
    // Public API (for external use if needed)
    // ============================================
    window.MicroBlogHub = {
        showToast,
        smoothScrollTo,
        CharacterCounter,
        CommentsModule,
        FormEnhancements,
        toggleProfileComments
    };
    function toggleProfileComments(postId) {
        const el = document.getElementById(`profile-comments-${postId}`);
        if (!el) return;
    
        if (el.style.display === 'none' || el.style.display === '') {
            el.style.display = 'block';
        } else {
            el.style.display = 'none';
        }
    }
    
    
    

    // Start the application
    init();

})();

// Comment Delete Confirmation
function confirmDeleteComment(event) {
    if (!confirm('Are you sure you want to delete this comment? This action cannot be undone.')) {
        event.preventDefault();
        return false;
    }
    return true;
}




// ===============================
// 🔔 Notifications (GLOBAL)
// ===============================

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie) {
        document.cookie.split(';').forEach(cookie => {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            }
        });
    }
    return cookieValue;
}


function openNotificationPopup() {
    const popup = document.getElementById('notificationPopup');
    if (!popup) return;

    popup.style.display = popup.style.display === 'block' ? 'none' : 'block';

    fetch('/notifications/mark-as-read/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        }
    })
    .then(res => res.json())
    .then(() => {
        const badge = document.querySelector('.notification-badge');
        if (badge) badge.remove();
    })
    .catch(err => console.error('Notification error:', err));
}

function closeNotificationPopup() {
    const popup = document.getElementById('notificationPopup');
    if (popup) popup.style.display = 'none';
}




