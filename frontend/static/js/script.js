async function regFunction(event) {
    event.preventDefault();  // Запобігаємо стандартну дію форми

    // Отримуємо форму та забираємо данні з неї
    const form = document.getElementById('registration-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        // Перевіряємо успішність відповіді
        if (!response.ok) {
            // Отримуємо дані про помилку
            const errorData = await response.json();
            displayErrors(errorData);  // Відображення помилки
            return;  // Перериваємо виконання функції
        }

        const result = await response.json();

        if (result.message) {  // Перевіряємо наявність повідомлення про успішну реєстрацію
            window.location.href = '/pages/login';  // Перенаправляємо користувача на сторінку логіна
        } else {
            alert(result.message || 'Невідома помилка');
        }
    } catch (error) {
        console.error('Помилка:', error);
        alert('Сталася помилка під час реєстрації. Будь ласка, спробуйте ще раз.');
    }
}

async function loginFunction(event) {
    event.preventDefault();

    const form = document.getElementById('login-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.json();
            displayErrors(errorData);
            return;
        }

        const result = await response.json();

        if (result.message) {
            // Fetch user data to determine role
            const userResponse = await fetch('/auth/me/');
            
            if (!userResponse.ok) {
                console.error("Failed to fetch user data after login");
                window.location.href = '/pages/profile';  // Fallback to profile page
                return;
            }
            
            const userData = await userResponse.json();
            
            // Redirect based on role hierarchy (highest privilege first)
            if (userData.is_admin || userData.is_super_admin) {
                window.location.href = '/pages/admin/dashboard';
            } else if (userData.is_hospital_staff) {
                window.location.href = '/pages/hospital_staff/dashboard';
            } else if (userData.is_donor) {
                window.location.href = '/pages/donor/dashboard';
            } else {
                window.location.href = '/pages/profile';  // Default for basic users
            }
        } else {
            alert(result.message || 'Невідома помилка');
        }
    } catch (error) {
        console.error('Помилка:', error);
        alert('Виникла помилка при вході. Будь ласка, спробуйте ще раз.');
    }
}


async function logoutFunction() {
    try {
        // Надсилання POST-запиту для видалення куки на сервері
        let response = await fetch('/auth/logout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // Перевірка відповіді сервера
        if (response.ok) {
            // Перенаправляємо користувача на сторінку логіна
            window.location.href = '/pages/login';
        } else {
            // Читання можливого повідомлення про помилку від сервера
            const errorData = await response.json();
            console.error('Помилка при вході:', errorData.message || response.statusText);
        }
    } catch (error) {
        console.error('Помилка мережі', error);
    }
}


// Функція для відображення помилок
function displayErrors(errorData) {
    let message = 'Трапилася помилка';

    if (errorData && errorData.detail) {
        if (Array.isArray(errorData.detail)) {
            // Обробка масиву помилок
            message = errorData.detail.map(error => {
                if (error.type === 'string_too_short') {
                    return `Поле "${error.loc[1]}" має містити мінімум ${error.ctx.min_length} символів.`;
                }
                return error.msg || 'Трапилася помилка';
            }).join('\n');
        } else {
            // Обробка одиночної помилки
            message = errorData.detail || 'Трапилася помилка';
        }
    }

    // Відображення повідомлення про помилку
    alert(message);
}