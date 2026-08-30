import os
from datetime import date, timedelta

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("PLAYWRIGHT_BASE_URL", "http://127.0.0.1:8000")
ADMIN_USER = os.getenv("PLAYWRIGHT_ADMIN_USER")
ADMIN_PASSWORD = os.getenv("PLAYWRIGHT_ADMIN_PASSWORD")


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})

        page.goto(BASE_URL, wait_until="networkidle")
        assert page.get_by_role("heading", name="Tu próxima sesión empieza aquí.").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth === document.documentElement.clientWidth")

        page.goto(f"{BASE_URL}/actividades/iniciacion-wingfoil/", wait_until="networkidle")
        assert page.get_by_role("heading", name="Iniciación al wingfoil", exact=True).is_visible()

        page.get_by_label("Nombre").fill("Prueba navegador")
        page.get_by_label("Email o teléfono").fill("qa@example.com")
        page.get_by_label("¿Qué día prefieres?").fill(
            (date.today() - timedelta(days=1)).isoformat()
        )
        page.get_by_label("Personas").fill("2")
        page.get_by_role("button", name="Enviar solicitud").click()
        assert page.get_by_text("Elige una fecha de hoy en adelante.").is_visible()

        page.get_by_label("¿Qué día prefieres?").fill(
            (date.today() + timedelta(days=5)).isoformat()
        )
        page.get_by_role("button", name="Enviar solicitud").click()
        page.wait_for_url("**/enviada/")
        assert page.get_by_role("heading", name="Ya tenemos tu petición.").is_visible()
        assert page.get_by_text("Tu plaza todavía no está confirmada").is_visible()

        page.goto(f"{BASE_URL}/admin/", wait_until="networkidle")
        assert page.get_by_role("button", name="Iniciar sesión").is_visible()
        if ADMIN_USER and ADMIN_PASSWORD:
            page.get_by_label("Nombre de usuario").fill(ADMIN_USER)
            page.get_by_label("Contraseña").fill(ADMIN_PASSWORD)
            page.get_by_role("button", name="Iniciar sesión").click()
            page.wait_for_url(f"{BASE_URL}/admin/")
            assert page.get_by_text("Solicitudes de reserva", exact=True).is_visible()

            page.goto(
                f"{BASE_URL}/admin/marketplace/bookingrequest/?q=Prueba+navegador",
                wait_until="networkidle",
            )
            while page.get_by_text("Prueba navegador", exact=True).count():
                page.get_by_text("Prueba navegador", exact=True).first.click()
                page.get_by_role("link", name="Eliminar", exact=True).click()
                page.locator('input[type="submit"]').click()

        browser.close()
    print("Browser QA: OK")


if __name__ == "__main__":
    main()
