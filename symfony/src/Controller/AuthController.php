<?php

namespace App\Controller;

use App\Entity\User;
use App\Repository\UserRepository;
use Doctrine\ORM\EntityManagerInterface;
use Lexik\Bundle\JWTAuthenticationBundle\Services\JWTTokenManagerInterface;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\PasswordHasher\Hasher\UserPasswordHasherInterface;

class AuthController extends AbstractController
{
    public function register(
        Request $request,
        UserRepository $users,
        UserPasswordHasherInterface $hasher,
        EntityManagerInterface $em,
        JWTTokenManagerInterface $jwtManager
    ): JsonResponse {
        $data = json_decode($request->getContent(), true);
        if (!is_array($data)) {
            return new JsonResponse(['ok' => false, 'error' => 'invalid_json'], 400);
        }

        $email = strtolower(trim((string) ($data['email'] ?? '')));
        $password = (string) ($data['password'] ?? '');
        $name = trim((string) ($data['name'] ?? ''));

        if ($email === '' || $password === '' || $name === '') {
            return new JsonResponse(['ok' => false, 'error' => 'missing_fields'], 400);
        }
        if (strlen($password) < 8) {
            return new JsonResponse(['ok' => false, 'error' => 'password_too_short'], 400);
        }
        if ($users->findOneBy(['email' => $email])) {
            return new JsonResponse(['ok' => false, 'error' => 'email_taken'], 409);
        }

        $user = new User();
        $user->setEmail($email);
        $user->setName($name);
        $user->setPassword($hasher->hashPassword($user, $password));

        $em->persist($user);
        $em->flush();

        $token = $jwtManager->create($user);

        return new JsonResponse([
            'ok' => true,
            'token' => $token,
            'user' => [
                'id' => $user->getId(),
                'email' => $user->getEmail(),
                'name' => $user->getName(),
            ],
        ], 201);
    }
}
