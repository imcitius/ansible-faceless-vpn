Шаблон проекта ansible.

При создании нового репозитория проекта, нужно форкаться от этого проекта.
после того как проект форкнут, можно будет обновляться из апстрима, см. инструкции ниже.


Для уже имеющихся проектов:

добавляем апстрим в проект:
git remote add skeleton git@jgit.me:ansible/ansible-project-skeleton.git

Обновляем код из апстрима в текущий мастер:
git pull skeleton master --allow-unrelated-histories

далее смотрим на какие файлы гит скажет о наличии конфликтов, правим конфликты.

Ну и как обычно коммитим обновленный код в свой проект:
git add --all . ; git commit -a -m "update from upstream skeleton"; git push

Пример файла requirements.yml тут:
https://jgit.me/ansible/ansible-project-skeleton/snippets/27