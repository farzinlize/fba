<div align="center" dir="rtl">

<img alt="نشان پروژه از ترکیب انتزاعی سه حرف FBA ساخته شده و شکلی شبیه صاعقه دارد که از زمین گسترش می‌یابد" width="320" src="https://wu-clan.github.io/picx-images-hosting/logo/fba.png">

# FastAPI Best Architecture

راهکاری برای معماری بک‌اند در سطح سازمانی

[English](./README.md) | [چینی ساده‌شده](./README.zh-CN.md) | فارسی

[![GitHub](https://img.shields.io/github/license/fastapi-practices/fastapi_best_architecture)](https://github.com/fastapi-practices/fastapi_best_architecture/blob/master/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-%2300758f)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.0%2B-%23336791)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-%23778877)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
![Docker](https://img.shields.io/badge/Docker-%232496ED?logo=docker&logoColor=white)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?logo=discord&logoColor=white)](https://discord.com/invite/yNN3wTbVAC)
![Discord](https://img.shields.io/discord/1185035164577972344)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/fastapi-practices/fastapi_best_architecture)

</div>

<div dir="rtl">

## معماری سه‌لایه

معماری MVC یکی از الگوهای رایج در برنامه‌های وب پایتون است. این پروژه از معماری سه‌لایه و ساختار پوشه‌بندی مشخصی استفاده می‌کند که با ساختار متداول چندبرنامه‌ای در چارچوب‌هایی مانند Django و Spring Boot تفاوت دارد. می‌توانید این ساختار را متناسب با نیاز پروژهٔ خود تغییر دهید.

| بخش | Java | fastapi_best_architecture |
|-----|------|---------------------------|
| نمایش | controller | api |
| انتقال داده | dto | schema |
| منطق کسب‌وکار | service + impl | service |
| دسترسی به داده | dao / mapper | crud |
| مدل | model / entity | model |

## راهنما

برای اطلاعات بیشتر، [مستندات رسمی](https://fastapi-practices.github.io/fastapi_best_architecture_docs/) را ببینید.

## زبان‌ها

این راهنما به زبان‌های [انگلیسی](./README.md)، [چینی ساده‌شده](./README.zh-CN.md) و فارسی در دسترس است.
برای دریافت پیام‌های پاسخ و اعتبارسنجیِ ترجمه‌شده، سربرگ `Accept-Language` را با مقدار `fa-IR`، `en-US` یا `zh-CN` ارسال کنید. کدهای کوتاه `fa`، `en` و `zh` نیز پشتیبانی می‌شوند.
تنظیم `I18N_DEFAULT_LANGUAGE` زبان پیش‌فرض را برای درخواست‌های بدون این سربرگ مشخص می‌کند؛ مقدار پیش‌فرض فعلی `zh-CN` است.
مستندات توسعه‌دهندگان، توضیحات API و پیام‌های خارج از سامانهٔ ترجمه به زبان انگلیسی هستند.

## حامیان مالی

<div align="center">
  <table>
    <tr>
      <td align="center">
        <a href="https://claude.uy/home">
          <img src="https://purple-sun-4f5a.wuyao1243.workers.dev/" alt="Claude.uy" width="400">
        </a>
      </td>
    </tr>
  </table>
</div>

## مشارکت‌کنندگان

<a href="https://github.com/fastapi-practices/fastapi_best_architecture/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=fastapi-practices/fastapi_best_architecture"/>
</a>

## سپاس ویژه

- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/latest/)
- [SQLAlchemy](https://docs.sqlalchemy.org/en/20/)
- [Casbin](https://casbin.org/zh/)
- [Ruff](https://beta.ruff.rs/docs/)
- ...

## ارتباط با جامعهٔ پروژه

[Discord](https://wu-clan.github.io/homepage/)

## مجوز

این پروژه تحت شرایط مجوز [MIT](https://github.com/fastapi-practices/fastapi_best_architecture/blob/master/LICENSE) منتشر شده است.

[![Stargazers over time](https://starchart.cc/fastapi-practices/fastapi_best_architecture.svg?variant=adaptive)](https://starchart.cc/fastapi-practices/fastapi_best_architecture)

</div>
